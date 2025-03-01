import time
import base64
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, EqualTo
import os
from google.cloud import storage
import requests

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

# Load Meshy API Key
API_KEY = os.environ.get("MESHY_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"} if API_KEY else {}

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(256), nullable=False)
    model_url = db.Column(db.String(256), nullable=True)
    task_id = db.Column(db.String(64), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms (unchanged)
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
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Unchanged signup logic
    form = SignupForm()
    if form.validate_on_submit():
        try:
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already exists.')
                return redirect(url_for('signup'))
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully!')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during signup. Please try again.')
            return redirect(url_for('signup'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Unchanged login logic
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('upload'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
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
            app.logger.info("Image read successfully")

            # Upload image to GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket(os.environ['BUCKET_NAME'])
            filename = f'images/{current_user.id}/{image_file.filename}'
            blob = bucket.blob(filename)
            blob.upload_from_string(image_bytes, content_type=image_file.content_type)
            image_url = blob.public_url
            app.logger.info(f"Image uploaded to {image_url}")

            if not API_KEY:
                flash('Meshy API key not configured.')
                return redirect(url_for('upload'))

            image_data_uri = image_to_data_uri(image_bytes, image_file.content_type)
            payload = {
                "image_url": image_data_uri,
                "enable_pbr": False,
                "should_remesh": True,
                "should_texture": True
            }
            app.logger.info("Calling Meshy API")
            response = requests.post("https://api.meshy.ai/openapi/v1/image-to-3d", json=payload, headers=HEADERS, timeout=10)
            response.raise_for_status()
            task_data = response.json()
            task_id = task_data.get("result")
            if not task_id:
                app.logger.error(f"No task ID received: {task_data}")
                flash("Task ID not received from API.")
                return redirect(url_for('upload'))
            app.logger.info(f"Task created: {task_id}")

            model = Model(user_id=current_user.id, image_url=image_url, task_id=task_id, model_url=None)
            db.session.add(model)
            db.session.commit()
            flash(f"Task key generated: {task_id}")
            return redirect(url_for('models'))

        except requests.RequestException as e:
            app.logger.error(f"Meshy API error: {str(e)}")
            flash(f'Meshy API error: {str(e)}')
            return redirect(url_for('upload'))
        except Exception as e:
            app.logger.error(f"Upload error: {str(e)}")
            flash(f'Upload failed: {str(e)}')
            return redirect(url_for('upload'))
    return render_template('upload.html', form=form)

@app.route('/status/<int:model_id>', methods=['GET'])
@login_required
def status(model_id):
    model = Model.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    if model.model_url:
        return jsonify({"status": "SUCCEEDED", "model_url": model.model_url})
    try:
        task_response = requests.get(f"https://api.meshy.ai/openapi/v1/image-to-3d/{model.task_id}", headers=HEADERS, timeout=10)
        task_response.raise_for_status()
        task_status = task_response.json()
        status = task_status.get("status")
        progress = task_status.get("progress", 0)
        app.logger.info(f"Task {model.task_id} status: {status}, Progress: {progress}%")

        if status == "SUCCEEDED":
            model_urls = task_status.get("model_urls", {})
            glb_url = model_urls.get("glb")
            if glb_url:
                glb_response = requests.get(glb_url, timeout=10)
                glb_response.raise_for_status()
                model_content = glb_response.content
                storage_client = storage.Client()
                bucket = storage_client.bucket(os.environ['BUCKET_NAME'])
                model_filename = f'models/{current_user.id}/{model.id}.glb'
                model_blob = bucket.blob(model_filename)
                model_blob.upload_from_string(model_content, content_type='model/gltf-binary')
                model.model_url = model_blob.public_url
                db.session.commit()
                app.logger.info(f"Model uploaded to {model.model_url}")
                return jsonify({"status": "SUCCEEDED", "model_url": model.model_url})
            else:
                app.logger.error("No GLB URL in task response")
                return jsonify({"status": "FAILED", "error": "No GLB URL"})
        elif status == "IN_PROGRESS":
            return jsonify({"status": "IN_PROGRESS", "progress": progress})
        else:
            return jsonify({"status": status})
    except requests.RequestException as e:
        app.logger.error(f"Status check error: {str(e)}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500

@app.route('/models')
@login_required
def models():
    user_models = Model.query.filter_by(user_id=current_user.id).all()
    app.logger.info(f"Found {len(user_models)} models for user {current_user.id}")
    return render_template('models.html', models=user_models)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admins only.')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin.html', users=users)

# Initialize database
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Admin user 'admin' created with password 'admin123'")
    else:
        if not admin.is_admin:
            admin.is_admin = True
            db.session.commit()
            app.logger.info("Updated existing 'admin' user to is_admin=True")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) #cs