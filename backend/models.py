from extensions import db, login_manager
from flask_login import UserMixin

class User(UserMixin, db.Model):
    
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}  
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    survey_data = db.Column(db.Text, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(50), nullable=True)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    objectives = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Float, default=0.0)
    chats = db.relationship('Chat', backref='topic', lazy=True, cascade="all, delete-orphan")
    shared_with = db.Column(db.JSON, default=[])  # New field to track users with whom the topic is shared

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True} 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    survey_data = db.Column(db.Text, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(50), nullable=True)
    points = db.Column(db.Integer, default=0)  # Track user points
    badges = db.Column(db.JSON, default={})  # Track user badges and achievements


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    user_correct = db.Column(db.Boolean, nullable=True)
    
class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    responses = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
