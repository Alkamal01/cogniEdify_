from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from extensions import db

notifications_blueprint = Blueprint('notifications', __name__)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)

@notifications_blueprint.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifications = Notification.query.filter_by(user_id=user_id).all()
    return jsonify([notification.to_dict() for notification in notifications]), 200

@notifications_blueprint.route('/notifications', methods=['POST'])
@jwt_required()
def create_notification():
    user_id = get_jwt_identity()
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({"message": "Message is required"}), 400

    new_notification = Notification(user_id=user_id, message=message)
    db.session.add(new_notification)
    db.session.commit()

    return jsonify(new_notification.to_dict()), 201

@notifications_blueprint.route('/notifications/<int:id>', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(id):
    user_id = get_jwt_identity()
    notification = Notification.query.filter_by(user_id=user_id, id=id).first()

    if not notification:
        return jsonify({"message": "Notification not found"}), 404

    notification.is_read = True
    db.session.commit()

    return jsonify(notification.to_dict()), 200
