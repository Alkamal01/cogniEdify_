from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') 
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') 
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') 
    UPLOAD_FOLDER = 'uploads/'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'csv', 'doc', 'docx'}
    OAUTH_CREDENTIALS = {
        'google': {
            'id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET')
        }
    }

    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
