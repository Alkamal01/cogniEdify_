from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Topic, User, db

topics_blueprint = Blueprint('topics', __name__)

@topics_blueprint.route('/topics', methods=['POST'])
@jwt_required()
def create_topic():
    data = request.get_json()
    title = data.get('title')
    objectives = data.get('objectives')
    user_id = get_jwt_identity()
    new_topic = Topic(user_id=user_id, title=title, objectives=objectives)
    db.session.add(new_topic)
    db.session.commit()
    return jsonify({"message": "Topic created successfully", "topic_id": new_topic.id}), 201

@topics_blueprint.route('/topics/<int:topic_id>', methods=['GET'])
@jwt_required()
def get_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    return jsonify({
        "topic": {
            "id": topic.id,
            "title": topic.title,
            "objectives": topic.objectives,
            "progress": topic.progress
        }
    }), 200

@topics_blueprint.route('/topics/<int:topic_id>/share', methods=['POST'])
@jwt_required()
def share_topic(topic_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    topic = Topic.query.filter_by(id=topic_id, user_id=user_id).first_or_404()
    
    shared_with_username = data.get('username')
    shared_user = User.query.filter_by(username=shared_with_username).first()
    
    if not shared_user:
        return jsonify({"message": "User not found."}), 404

    if shared_user.id == user_id:
        return jsonify({"message": "You cannot share a topic with yourself."}), 400

    if shared_user.id in topic.shared_with:
        return jsonify({"message": "Topic already shared with this user."}), 400

    topic.shared_with.append(shared_user.id)
    db.session.commit()

    return jsonify({"message": f"Topic '{topic.title}' shared with {shared_user.username}."}), 200

@topics_blueprint.route('/topics/shared', methods=['GET'])
@jwt_required()
def get_shared_topics():
    user_id = get_jwt_identity()
    shared_topics = Topic.query.filter(Topic.shared_with.contains([user_id])).all()

    shared_topics_data = [{
        "id": topic.id,
        "title": topic.title,
        "objectives": topic.objectives,
        "progress": topic.progress,
        "shared_by": User.query.get(topic.user_id).username
    } for topic in shared_topics]

    return jsonify({"shared_topics": shared_topics_data}), 200

@topics_blueprint.route('/topics/<int:topic_id>/collaborate', methods=['POST'])
@jwt_required()
def collaborate_on_topic(topic_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    topic = Topic.query.filter_by(id=topic_id).filter(
        (Topic.user_id == user_id) | (Topic.shared_with.contains([user_id]))
    ).first_or_404()
    
    message = data['message']
    prompt = (
        f"You are facilitating a collaborative learning session. "
        f"Users are collaborating on the topic '{topic.title}'. "
        f"Respond to the following message from a participant: {message}. "
    )

    ai_response = llm(prompt)
    
    # Store the interaction in the database
    chat = Chat(topic_id=topic_id, user_message=message, ai_response=ai_response)
    db.session.add(chat)
    db.session.commit()

    return jsonify({'response': ai_response}), 200
