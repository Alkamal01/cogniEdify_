from flask import Blueprint, request, jsonify
from extensions import db
from models import Survey
from flask_jwt_extended import jwt_required, get_jwt_identity

surveys_blueprint = Blueprint('surveys', __name__)

@surveys_blueprint.route('/surveys', methods=['POST'])
@jwt_required()
def submit_survey():
    data = request.get_json()
    title = data.get('title')
    responses = data.get('responses')

    if not title or not responses:
        return jsonify({"message": "Title and responses are required"}), 400

    user_id = get_jwt_identity()

    existing_survey = Survey.query.filter_by(user_id=user_id, title=title).first()

    if existing_survey:
        existing_survey.responses = responses
    else:
        new_survey = Survey(user_id=user_id, title=title, responses=responses)
        db.session.add(new_survey)

    db.session.commit()

    return jsonify({"message": "Survey submitted successfully"}), 201

@surveys_blueprint.route('/surveys', methods=['GET'])
@jwt_required()
def get_surveys():
    user_id = get_jwt_identity()
    surveys = Survey.query.filter_by(user_id=user_id).all()

    surveys_data = [{
        "id": survey.id,
        "title": survey.title,
        "responses": survey.responses,
    } for survey in surveys]

    return jsonify(surveys_data), 200
