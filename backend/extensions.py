from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_oauthlib.client import OAuth

db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()
oauth = OAuth()
