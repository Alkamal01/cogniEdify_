from flask import Flask
from extensions import db, login_manager, jwt, oauth
from flask_mail import Mail
from dotenv import load_dotenv
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
import logging
from flask_migrate import Migrate

app = Flask(__name__)
load_dotenv()

migrate = Migrate(app, db)  

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# File path to save the FAISS index
FAISS_INDEX_PATH = 'faiss_index'

# Initialize global variables
vectorstore = None

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') 
    app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER') 
    app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER') 
    app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

    # Initialize the Mail instance
    db.init_app(app)
    mail = Mail(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    oauth.init_app(app)
    mail.init_app(app)
    

    # Initialize the embedding function
    embedding = OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_API_KEY'))

    # Check if the FAISS index exists, otherwise defer initialization until data is available
    global vectorstore
    if os.path.exists(FAISS_INDEX_PATH):
        logger.info("Loading existing FAISS index.")
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embedding, allow_dangerous_deserialization=True)

    else:
        logger.info("No existing FAISS index found. Initialization will be deferred until data is available.")

    from routes.auth import auth_blueprint
    from routes.topics import topics_blueprint
    from routes.surveys import surveys_blueprint
    from routes.interactions import interactions_blueprint
    from routes.progress import progress_blueprint
    # from routes.language import language_blueprint

    app.register_blueprint(auth_blueprint, url_prefix='/api')
    app.register_blueprint(surveys_blueprint, url_prefix='/api')
    app.register_blueprint(topics_blueprint, url_prefix='/api')
    app.register_blueprint(interactions_blueprint, url_prefix='/api')
    app.register_blueprint(progress_blueprint, url_prefix='/api')
    # app.register_blueprint(language_blueprint, url_prefix='/api')

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)