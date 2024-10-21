from flask import Blueprint, current_app as app, render_template, request, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_login import login_user, logout_user, login_required
from extensions import db, oauth
from models import User
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import os
import re
from canister import call_canister, query_canister
import requests
import base64
import json
import cbor2
from dotenv import load_dotenv

load_dotenv()
auth_blueprint = Blueprint('auth', __name__)
mail = Mail()


CANISTER_URL = os.getenv('CANISTER_URL', 'http://127.0.0.1:8000')
CANISTER_ID = os.getenv('CANISTER_ID')

def create_user_in_canister(user_id, username, email):
    try:
        # Prepare the arguments in CBOR format
        args = {
            "id": user_id,
            "username": username,
            "email": email
        }

        # Encode the arguments using CBOR
        cbor_data = cbor2.dumps(args)
        
        # Encode the CBOR data in base64
        encoded_args = base64.b64encode(cbor_data).decode()

        # Prepare the payload
        payload = {
            "arg": encoded_args,
            "method_name": "createUser",
            "canister_id": CANISTER_ID
        }

        headers = {
            "Content-Type": "application/cbor"
        }

        # Send the request with the correct content type
        response = requests.post(f'{CANISTER_URL}/api/v2/canister/{CANISTER_ID}/call', json=payload, headers=headers)
        
        # Log the raw response
        app.logger.info(f"Raw response from canister: {response.content}")

        # Attempt to parse the response as JSON
        try:
            response_json = response.json()
            app.logger.info(f"Parsed response from canister: {response_json}")
            return response_json
        except ValueError:
            app.logger.warning("Response was not valid JSON.")
            return {"status": "invalid JSON", "response": response.text}

    except Exception as e:
        app.logger.error(f"Error communicating with canister: {str(e)}")
        raise
    
@auth_blueprint.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        app.logger.info(f"Received data: {data}")
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not username or not email or not password or not confirm_password or not first_name or not last_name:
            app.logger.warning("Missing required fields")
            return jsonify({"message": "Missing required fields"}), 400

        if password != confirm_password:
            app.logger.warning("Passwords do not match")
            return jsonify({"message": "Passwords do not match"}), 400

        if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"\d", password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            app.logger.warning("Password does not meet criteria")
            return jsonify({"message": "Password must be at least 8 characters long, include an uppercase letter, a number, and a special character"}), 400

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            app.logger.warning("User with this email already exists")
            return jsonify({"message": "User with this email already exists"}), 400

        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            app.logger.warning("Username already exists")
            return jsonify({"message": "Username already exists"}), 400

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = User(username=username, email=email, password=hashed_password, first_name=first_name, last_name=last_name)

        try:
            # Create user in the canister
            canister_response = create_user_in_canister(new_user.id, new_user.username, new_user.email)
            app.logger.info(f"Canister response: {canister_response}")

            # Check the canister response for success
            if canister_response:
                db.session.add(new_user)
                db.session.commit()
                send_verification_email(new_user)
                return jsonify({"message": "User registered successfully. Please verify your email."}), 201
            else:
                app.logger.error(f"Failed to register user in canister. Response: {canister_response}")
                return jsonify({"message": "Failed to register user in canister"}), 500

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during registration: {str(e)}")
            return jsonify({"message": str(e)}), 500

    except Exception as outer_e:
        app.logger.error(f"Unexpected error during registration: {str(outer_e)}")
        return jsonify({"message": "An unexpected error occurred during registration."}), 500


def send_verification_email(user):
    try:
        token = generate_confirmation_token(user.email)
        app.logger.info(f"Generated token: {token}")
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        app.logger.info(f"Confirmation URL: {confirm_url}")
        html = render_template('email_verification.html', confirm_url=confirm_url)
        app.logger.info("Rendered email template successfully.")
        subject = "Please confirm your email"
        send_email(user.email, subject, html)
    except Exception as e:
        app.logger.error(f"Error in send_verification_email: {str(e)}")
        raise e


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

@auth_blueprint.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        return jsonify({"message": "The confirmation link is invalid or has expired."}), 400
    
    user = User.query.filter_by(email=email).first_or_404()
    
    if user.email_verified:
        return jsonify({"message": "Account already confirmed. Please login."}), 200
    else:
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "You have confirmed your account. Thanks!"}), 200


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=os.getenv('MAIL_DEFAULT_SENDER')
    )
    try:
        mail.send(msg)
        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", str(e))
        

@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        if not user.email_verified:
            return jsonify({"message": "Please verify your email first."}), 401

        # Validate against canister
        canister_user = get_user_from_canister(user.id)
        if not canister_user:
            return jsonify({"message": "User not found in canister"}), 401

        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token, user_id=user.id), 200  # Include user_id in the response

    return jsonify({"message": "Invalid credentials"}), 401



@auth_blueprint.route('/google_login')
def google_login():
    google = oauth.remote_app(
        'google',
        consumer_key=app.config['OAUTH_CREDENTIALS']['google']['id'],
        consumer_secret=app.config['OAUTH_CREDENTIALS']['google']['secret'],
        request_token_params={
            'scope': 'email',
        },
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
    )
    return google.authorize(callback=url_for('auth.google_authorized', _external=True))


@auth_blueprint.route('/google_authorized')
def google_authorized():
    response = google.authorized_response()
    if response is None or response.get('access_token') is None:
        return jsonify({"message": "Access denied: reason={} error={}".format(
            request.args['error_reason'],
            request.args['error_description']
        )}), 401

    access_token = response['access_token']
    google = oauth.remote_app('google')
    google.tokengetter(lambda: (access_token, ''))
    user_info = google.get('userinfo')
    user_data = user_info.data

    user = User.query.filter_by(email=user_data['email']).first()
    if not user:
        user = User(
            username=user_data['email'],
            email=user_data['email'],
            first_name=user_data['given_name'],
            last_name=user_data['family_name'],
            password='',
            email_verified=True
        )
        db.session.add(user)
        db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200


@auth_blueprint.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully."}), 200


@auth_blueprint.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    try:
        email = confirm_token(token)
    except:
        return jsonify({"message": "The reset link is invalid or has expired."}), 400
    
    data = request.get_json()
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not password or not confirm_password or password != confirm_password:
        return jsonify({"message": "Passwords do not match or are invalid."}), 400

    if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"\d", password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return jsonify({"message": "Password must be at least 8 characters long, include an uppercase letter, a number, and a special character"}), 400

    user = User.query.filter_by(email=email).first_or_404()

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
    user.password = hashed_password
    db.session.commit()

    return jsonify({"message": "Your password has been updated!"}), 200

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

@auth_blueprint.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"message": "Invalid email address."}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        token = generate_reset_token(user.email)
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        html = render_template('email_password_reset.html', reset_url=reset_url)
        subject = "Password Reset Request"
        send_email(user.email, subject, html)
    
    return jsonify({"message": "An email has been sent with instructions to reset your password."}), 200
