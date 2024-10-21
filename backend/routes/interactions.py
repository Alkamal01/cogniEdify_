from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Topic, User, Chat
from extensions import db
import openai
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.llms import OpenAI
from .files import handle_file_upload, vectorstore, FAISS_INDEX_PATH
import os
from dotenv import load_dotenv
from . language import translate_text

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

interactions_blueprint = Blueprint('interactions', __name__)
openai.api_key = os.getenv('OPENAI_API_KEY')
llm = OpenAI(temperature=0.7, max_tokens=1000, openai_api_key=openai.api_key)

interaction_counter = 0
SAVE_THRESHOLD = 10

@interactions_blueprint.route('/upload_file', methods=['POST'])
@jwt_required()
def upload_file():
    return handle_file_upload()


@interactions_blueprint.route('/interact', methods=['POST'])
@jwt_required()
def interact():
    global interaction_counter, vectorstore
    try:
        data = request.json
        logger.info(f"Received data: {data}")

        topic_id = data['topic_id']
        message = data['message']
        logger.info(f"Topic ID: {topic_id}, Message: {message}")

        topic = Topic.query.get_or_404(topic_id)
        logger.info(f"Topic retrieved: {topic.title}")

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        logger.info(f"User retrieved: {user.first_name}")

        # Check if the user's language is Hausa, Yoruba, or Igbo and translate if necessary
        if user.language in ['hau', 'yor', 'ibo']:
            source_lang = user.language
            target_lang = 'eng'
            # Translate the user's message to English
            translated_message = translate_text(message, source_lang, target_lang)
            logger.info(f"Translated Message to English: {translated_message}")
        else:
            translated_message = message

        # Retrieve recent interactions for performance analysis
        recent_chats = Chat.query.filter_by(topic_id=topic_id).order_by(Chat.timestamp.desc()).limit(5).all()
        struggling = any(chat.user_correct == False for chat in recent_chats)

        if struggling:
            content_adjustment = "Provide simpler explanations or additional resources."
        else:
            content_adjustment = "Proceed with the standard learning path."

        if interaction_counter == 0:
            ai_response = (
                f"Hello {user.first_name}, welcome to Cogniedify, your personal cognitive assistant tutor. "
                f"I will take you through the topic '{topic.title}'. Happy learning!"
            )
        else:
            prompt = (
                f"You are a highly skilled educator focused on personalized learning. "
                f"The user has the following learning preferences based on a recent survey: {user.survey_data}. "
                f"The user is currently learning about '{topic.title}'. "
                f"The objective of this topic is: {topic.objectives}. "
                f"{content_adjustment} "
                f"Incorporate a brief question or thought exercise to engage the user, as they prefer an interactive learning style. "
                f"Ensure the explanation stays focused on the objective and aligns with the user's learning preferences. "
                f"Use plain language, avoid unnecessary jargon, and ensure no hallucinations occur in your explanation. "
                f"Respond directly to the following question from the user: {translated_message}. "
                f"End the explanation by asking the user if they understood the content and if they need further clarification."
            )
            logger.info(f"Generated prompt: {prompt}")

            ai_response = llm(prompt)
            logger.info(f"AI Response: {ai_response}")

        # If the user's language is Hausa, Yoruba, or Igbo, translate the AI's response back to their language
        if user.language in ['hau', 'yor', 'ibo']:
            ai_response = translate_text(ai_response, target_lang, source_lang)
            logger.info(f"Translated AI Response to {user.language}: {ai_response}")

        # Store the interaction in the database
        chat = Chat(topic_id=topic_id, user_message=message, ai_response=ai_response)
        db.session.add(chat)
        db.session.commit()
        logger.info("Chat saved to database.")

        # Initialize vectorstore if it has not been created yet
        if vectorstore is None:
            logger.info("Initializing vectorstore with the first text.")
            vectorstore = FAISS.from_texts(
                [message, ai_response],
                OpenAIEmbeddings(openai_api_key=openai.api_key),
                metadatas=[{'topic_id': topic_id}, {'topic_id': topic_id}]
            )
        else:
            # Vectorize the user's message and AI response and store them in FAISS
            vectorstore.add_texts(
                [message, ai_response],
                metadatas=[{'topic_id': topic_id}, {'topic_id': topic_id}]
            )
        logger.info("Texts added to FAISS index.")

        interaction_counter += 1
        if interaction_counter >= SAVE_THRESHOLD:
            logger.info("Saving FAISS index to disk.")
            vectorstore.save_local(FAISS_INDEX_PATH)
            interaction_counter = 0

        return jsonify({'response': ai_response}), 200

    except Exception as e:
        logger.error(f"Error during interaction: {str(e)}")
        return jsonify({"error": "An error occurred during the interaction"}), 500


def generate_quiz_from_topic(topic, user):
    prompt = (
        f"You are a highly skilled educator focused on personalized learning. "
        f"The user has the following learning preferences based on a recent survey: {user.survey_data}. "
        f"The user has just completed learning about '{topic.title}'. "
        f"The objective of this topic is: {topic.objectives}. "
        f"Generate a quiz with multiple-choice questions to assess the user's understanding of the topic. "
        f"Ensure the questions are aligned with the topic objectives and tailored to the user's learning preferences. "
        f"Provide four possible answers for each question, with one correct answer."
    )

    # Call OpenAI to generate the quiz questions
    response = llm(prompt)
    quiz_questions = parse_quiz_response(response)

    return quiz_questions

def parse_quiz_response(response):
    # Parse the response from OpenAI to extract quiz questions and answers
    questions = []
    lines = response.split('\n')
    current_question = None
    for line in lines:
        if line.startswith("Question"):
            if current_question:
                questions.append(current_question)
            current_question = {"question": line, "options": [], "correct_answer": None}
        elif line.startswith("A)") or line.startswith("B)") or line.startswith("C)") or line.startswith("D)"):
            current_question["options"].append(line)
        elif "Correct Answer:" in line:
            current_question["correct_answer"] = line.split(": ")[1]
    if current_question:
        questions.append(current_question)
    return questions

def review_quiz(user_answers, topic, user):
    prompt = (
        f"You are a highly skilled educator focused on personalized learning. "
        f"The user has just completed a quiz on the topic '{topic.title}'. "
        f"The objective of this topic is: {topic.objectives}. "
        f"Review the user's answers and provide detailed feedback on each question. "
        f"Correct any mistakes and offer explanations to help the user understand the correct answers."
    )

    # Add the user's answers to the prompt
    for i, (question, answer) in enumerate(user_answers.items(), 1):
        prompt += f"\nQuestion {i}: {question}\nUser's Answer: {answer}"

    # Call OpenAI to generate the feedback
    response = llm(prompt)
    
    # Determine if the user struggled and adjust content accordingly
    struggling = any("Incorrect" in feedback for feedback in response.split('\n'))

    if struggling:
        additional_resources_prompt = (
            f"The user seems to be struggling with '{topic.title}'. "
            f"Provide additional resources, simpler explanations, or alternative ways to understand the material."
        )
        additional_resources = llm(additional_resources_prompt)
        response += f"\n\nAdditional Resources: {additional_resources}"

    # Provide personalized suggestions for improvement (Feedback Loops)
    improvement_suggestions_prompt = (
        f"The user has completed a quiz on the topic '{topic.title}' and struggled with some questions. "
        f"Based on the user's learning style ({user.survey_data}), provide personalized suggestions for improvement."
    )
    improvement_suggestions = llm(improvement_suggestions_prompt)
    response += f"\n\nSuggestions for Improvement: {improvement_suggestions}"

    # Recommend additional content (Content Recommendations)
    content_recommendations_prompt = (
        f"Based on the user's performance in the quiz and their learning preferences, suggest additional reading materials, "
        f"videos, or exercises that would help the user improve their understanding of the topic '{topic.title}'."
    )
    content_recommendations = llm(content_recommendations_prompt)
    response += f"\n\nContent Recommendations: {content_recommendations}"

    # Award points and badges
    correct_answers = sum(1 for line in response.split('\n') if "Correct!" in line)
    points_awarded = correct_answers * 10  # 10 points per correct answer
    user.points += points_awarded

    if correct_answers == len(user_answers):
        user.badges['Quiz Master'] = True

    db.session.commit()

    return response

@interactions_blueprint.route('/topics/<int:topic_id>/generate_quiz', methods=['POST'])
@jwt_required()
def generate_quiz(topic_id):
    user_id = get_jwt_identity()
    topic = Topic.query.filter_by(id=topic_id, user_id=user_id).first_or_404()
    user = User.query.get(user_id)

    if not topic.is_completed:
        return jsonify({"message": "You must complete the topic before accessing the quiz."}), 403
    
    quiz_data = generate_quiz_from_topic(topic, user)
    
    return jsonify({"quiz": quiz_data}), 200

@interactions_blueprint.route('/topics/<int:topic_id>/submit_quiz', methods=['POST'])
@jwt_required()
def submit_quiz(topic_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    topic = Topic.query.filter_by(id=topic_id, user_id=user_id).first_or_404()
    user = User.query.get(user_id)

    if not topic.is_completed:
        return jsonify({"message": "You must complete the topic before taking the quiz."}), 403
    
    user_answers = data.get('answers')
    feedback = review_quiz(user_answers, topic, user)

    return jsonify({"feedback": feedback, "points": user.points, "badges": user.badges}), 200

@interactions_blueprint.route('/get_chats/<int:topic_id>/download', methods=['GET'])
@jwt_required()
def download_chat_history(topic_id):
    try:
        user_id = get_jwt_identity()
        topic = Topic.query.filter_by(id=topic_id, user_id=user_id).first_or_404()
        chats = Chat.query.filter_by(topic_id=topic_id).order_by(Chat.timestamp.asc()).all()

        # Convert chat history to a downloadable format (e.g., PDF, text)
        chat_history = "\n".join([f"User: {chat.user_message}\nAI: {chat.ai_response}" for chat in chats])
        
        # For PDF conversion, use a library like FPDF or ReportLab
        response = make_response(chat_history)
        response.headers['Content-Disposition'] = f'attachment; filename=topic_{topic_id}_chat_history.txt'
        response.mimetype = 'text/plain'

        return response

    except Exception as e:
        logger.error(f"Error downloading chat history: {str(e)}")
        return jsonify({"error": "An error occurred while downloading the chat history"}), 500

@interactions_blueprint.route('/search_chats/<int:topic_id>', methods=['GET'])
@jwt_required()
def search_chats(topic_id):
    try:
        user_id = get_jwt_identity()
        query = request.args.get('query')

        # Perform a similarity search in the vector store
        results = vectorstore.similarity_search(query, k=5)  # Top 5 results

        # Retrieve chat entries for the results
        matched_chats = []
        for result in results:
            if result.metadata['topic_id'] == topic_id:
                chat = Chat.query.filter_by(user_message=result.text, topic_id=topic_id).first()
                matched_chats.append({
                    "user_message": chat.user_message,
                    "ai_response": chat.ai_response,
                    "timestamp": chat.timestamp
                })

        return jsonify(matched_chats), 200

    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        return jsonify({"error": "An error occurred during the search"}), 500

@interactions_blueprint.route('/get_chats/<int:topic_id>', methods=['GET'])
@jwt_required()
def get_chats(topic_id):
    try:
        user_id = get_jwt_identity()
        topic = Topic.query.filter_by(id=topic_id, user_id=user_id).first_or_404()
        chats = Chat.query.filter_by(topic_id=topic_id).order_by(Chat.timestamp.asc()).all()

        chat_history = [{"user_message": chat.user_message, "ai_response": chat.ai_response, "timestamp": chat.timestamp} for chat in chats]

        return jsonify(chat_history), 200

    except Exception as e:
        logger.error(f"Error retrieving chats: {str(e)}")
        return jsonify({"error": "An error occurred while retrieving the chat history"}), 500

@interactions_blueprint.route('/delete_topic/<int:topic_id>', methods=['DELETE'])
@jwt_required()
def delete_topic(topic_id):
    try:
        user_id = get_jwt_identity()
        topic = Topic.query.filter_by(id=topic_id, user_id=user_id).first_or_404()

        db.session.delete(topic)
        db.session.commit()

        logger.info(f"Topic {topic_id} and associated chats deleted successfully.")
        return jsonify({"message": "Topic and associated chats deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting topic {topic_id}: {str(e)}")
        return jsonify({"error": "An error occurred while deleting the topic"}), 500

@interactions_blueprint.route('/leaderboard', methods=['GET'])
@jwt_required()
def leaderboard():
    users = User.query.order_by(User.points.desc()).limit(10).all()

    leaderboard_data = [{"username": user.username, "points": user.points} for user in users]

    return jsonify({"leaderboard": leaderboard_data}), 200

@interactions_blueprint.route('/achievements', methods=['GET'])
@jwt_required()
def achievements():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    return jsonify({"points": user.points, "badges": user.badges}), 200

@interactions_blueprint.before_request
def before_request():
    logger.info(f"Handling request: {request.method} {request.path}")

@interactions_blueprint.after_request
def after_request(response):
    logger.info(f"Request handled with status: {response.status_code}")
    return response

