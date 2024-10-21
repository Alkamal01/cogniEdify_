from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Topic

progress_blueprint = Blueprint('progress', __name__)

@progress_blueprint.route('/progress', methods=['GET'])
@jwt_required()
def view_progress():
    user_id = get_jwt_identity()
    topics = Topic.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "topic_id": topic.id,
        "title": topic.title,
        "progress": topic.progress
    } for topic in topics]), 200
