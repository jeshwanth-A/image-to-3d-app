\import logging
import time
import base64
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, EqualTo
import os
from google.cloud import storage
import requests
from sqlalchemy import inspect

# Setup Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-for-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Setup logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # Log SQL statements

# Load Meshy API Key
API_KEY = os.environ.get("MESHY_API_KEY")
if not API_KEY:
    app.logger.warning("MESHY_API_KEY not set; upload functionality will fail.")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"} if API_KEY else {}

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Set to 256

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(256), nullable=False)
    model_url = db.Column(db.String(256), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class UploadForm(FlaskForm):
    image = FileField('Image', validators=[DataRequired()])
    submit = SubmitField('Upload')

# Helper Function
def image_to_data_uri(image_bytes: bytes, content_type: str) -> str:
    base64_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{content_type};base64,{base64_data}"

# Routes
@app.route('/')
def index():
    app.logger.info(f"Accessing index with DATABASE_URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    app.logger.info("Signup route accessed")
    if form.validate_on_submit():
        try:
            app.logger.info(f"Checking if username {form.username.data} exists")
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already exists.')
                return redirect(url_for('signup'))
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            app.logger.info(f"Generated password hash: {user.password_hash}")
            app.logger.info(f"Password hash length: {len(user.password_hash)}")
            db.session.add(user)
            db.session.commit()
            app.logger.info(f"User {form.username.data} created successfully")
            flash('Account created successfully!')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Signup error: {str(e)}", exc_info=True)
            flash('An error occurred during signup. Please try again.')
            return redirect(url_for('signup'))
    elif request.method == 'POST':
        app.logger.info("Form validation failed")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}")
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    app.logger.info("Login route accessed")
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                app.logger.info(f"User {form.username.data} logged in")
                return redirect(url_for('upload'))
            flash('Invalid username or password.')
            app.logger.warning(f"Failed login attempt for {form.username.data}")
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}", exc_info=True)
            flash('An error occurred during login. Please try again.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    app.logger.info(f"User {current_user.username} logged out")
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        try:
            app.logger.info(f"Uploading image for user {current_user.id}")
            image_file = form.image.data
            image_bytes = image_file.read()

            storage_client = storage.Client()
            bucket = storage_client.bucket(os.environ['BUCKET_NAME'])
            filename = f'images/{current_user.id}/{image_file.filename}'
            blob = bucket.blob(filename)
            blob.upload_from_string(image_bytes, content_type=image_file.content_type)
            image_url = blob.public_url
            app.logger.info(f"Image uploaded to {image_url}")

            if not API_KEY:
                flash('Meshy API key not configured. Model generation unavailable.')
                return redirect(url_for('upload'))

            image_data_uri = image_to_data_uri(image_bytes, image_file.content_type)
            payload = {"image_url": image_data_uri, "enable_pbr": False, "should_remesh": True, "should_texture": True}
            response = requests.post("https://api.meshy.ai/openapi/v1/image-to-3d", json=payload, headers=HEADERS)
            response.raise_for_status()
            task_data = response.json()
            task_id = task_data.get("result")
            if not task_id:
                flash("Task ID not received from API.")
                return redirect(url_for('upload'))
            app.logger.info(f"Task created: {task_id}")

            max_attempts = 60
            attempt = 0
            while attempt < max_attempts:
                time.sleep(10)
                task_response = requests.get(f"https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}", headers=HEADERS)
                task_status = task_response.json()
                status = task_status.get("status")
                progress = task_status.get("progress", 0)
                app.logger.info(f"Task status: {status}, Progress: {progress}%")
                if status == "SUCCEEDED":
                    model_urls = task_status.get("model_urls", {})
                    glb_url = model_urls.get("glb")
                    if glb_url:
                        app.logger.info(f"Model URL: {glb_url}")
                        model_response = requests.get(glb_url)
                        model_content = model_response.content
                        model_filename = f'models/{current_user.id}/{image_file.filename}.glb'
                        model_blob = bucket.blob(model_filename)
                        model_blob.upload_from_string(model_content, content_type='model/gltf-binary')
                        model_url = model_blob.public_url
                        app.logger.info(f"Model uploaded to {model_url}")
                        model = Model(user_id=current_user.id, image_url=image_url, model_url=model_url)
                        db.session.add(model)
                        db.session.commit()
                        flash('Image uploaded and model generated!')
                        return redirect(url_for('models'))
                    else:
                        flash('Model URL not found in API response.')
                        return redirect(url_for('upload'))
                elif status in ["FAILED", "CANCELED"]:
                    flash(f'Task {status.lower()}.')
                    return redirect(url_for('upload'))
                attempt += 1
            flash('Task is taking longer than expected. Please check back later.')
            return redirect(url_for('models'))
        except Exception as e:
            app.logger.error(f"Error in upload route: {str(e)}", exc_info=True)
            flash('An error occurred during upload. Please try again.')
            return redirect(url_for('upload'))
    elif request.method == 'POST':
        app.logger.info("Upload form validation failed")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}")
    return render_template('upload.html', form=form)

@app.route('/models')
@login_required
def models():
    app.logger.info(f"Fetching models for user {current_user.id}")
    user_models = Model.query.filter_by(user_id=current_user.id).all()
    return render_template('models.html', models=user_models)

# Initialize database with debugging
with app.app_context():
    app.logger.info(f"Using DATABASE_URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.logger.info("Attempting to create database tables...")
    db.create_all()
    inspector = inspect(db.engine)
    if 'User' in inspector.get_table_names():
        columns = inspector.get_columns('User')
        app.logger.info(f"User table columns: {[(col['name'], col['type']) for col in columns]}")
    else:
        app.logger.error("User table not found after db.create_all()")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) #vs