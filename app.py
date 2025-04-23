import time
import base64
import logging
import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, EqualTo
import os
from google.cloud import storage
import requests
from werkzeug.middleware.proxy_fix import ProxyFix

# Setup Flask app
app = Flask(__name__)
# Make sure this is set to a constant value in your environment, not generated randomly
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key-for-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True  # <--- Add this line for debugging
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# If running behind a proxy (like on Cloud Run), add:
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Setup logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Load Tripo API Key (use the secret for Tripo, not Meshy)
API_KEY = os.environ.get("TRIPO_API_KEY")
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
    name = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)  # Add timestamp

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
    name = StringField('Model Name (optional)')
    submit = SubmitField('Upload')

class RenameModelForm(FlaskForm):
    name = StringField('Model Name', validators=[DataRequired()])
    submit = SubmitField('Rename')

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
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                if user.is_admin:
                    return redirect(url_for('admin_panel'))
                return redirect(url_for('upload'))
            flash('Invalid username or password.')
        except Exception as e:
            flash('An error occurred during login. Please try again.')
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

            # Upload image to Google Cloud Storage
            storage_client = storage.Client()
            bucket = storage_client.bucket(os.environ['BUCKET_NAME'])
            filename = f'images/{current_user.id}/{image_file.filename}'
            blob = bucket.blob(filename)
            blob.upload_from_string(image_bytes, content_type=image_file.content_type)
            image_url = blob.public_url
            app.logger.info(f"Image uploaded to {image_url}")

            if not API_KEY:
                flash('Tripo API key not configured.')
                return redirect(url_for('upload'))

            # Step 1: Upload image to Tripo API
            app.logger.info("Uploading image to Tripo API")
            tripo_upload_url = "https://api.tripo3d.ai/v2/openapi/upload"
            files = {'file': (image_file.filename, image_bytes, image_file.content_type)}
            upload_headers = {"Authorization": f"Bearer {API_KEY}"}
            upload_response = requests.post(tripo_upload_url, headers=upload_headers, files=files)
            if upload_response.status_code == 403:
                app.logger.error("Tripo upload 403 Forbidden: Check your TRIPO_API_KEY and Tripo account permissions.")
                flash("Tripo API error: Forbidden (check your API key and permissions).")
                return redirect(url_for('upload'))
            upload_response.raise_for_status()
            upload_data = upload_response.json()
            if upload_data.get("code") != 0:
                app.logger.error(f"Tripo upload failed: {upload_data}")
                flash(f"Tripo upload failed: {upload_data.get('message', 'Unknown error')}")
                return redirect(url_for('upload'))
            image_token = upload_data["data"]["image_token"]
            app.logger.info(f"Tripo image token: {image_token}")

            # Step 2: Start image-to-3D task with Tripo API
            app.logger.info("Calling Tripo API to start image-to-3D task")
            tripo_task_url = "https://api.tripo3d.ai/v2/openapi/task"
            payload = {
                "type": "image_to_model",
                "file": {
                    "type": "jpg" if "jpg" in image_file.filename.lower() else "png",
                    "file_token": image_token
                },
                "model_version": "v2.5-20250123",
                "texture": True,
                "pbr": False
            }
            task_response = requests.post(tripo_task_url, headers=HEADERS, json=payload)
            task_response.raise_for_status()
            task_data = task_response.json()
            if task_data.get("code") != 0:
                app.logger.error(f"Tripo task creation failed: {task_data}")
                flash(f"Tripo task creation failed: {task_data.get('message', 'Unknown error')}")
                return redirect(url_for('upload'))
            task_id = task_data["data"]["task_id"]
            app.logger.info(f"Task created: {task_id}")

            # Save task details to database
            base_name = os.path.splitext(image_file.filename)[0]
            model_name = form.name.data.strip() if form.name.data and form.name.data.strip() else base_name
            model = Model(user_id=current_user.id, image_url=image_url, task_id=task_id, model_url=None, name=model_name)
            db.session.add(model)
            db.session.commit()
            flash(f"Task key generated: {task_id}")
            return redirect(url_for('models'))
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 403:
                app.logger.error("Tripo API 403 Forbidden: Check your TRIPO_API_KEY and Tripo account permissions.")
                flash("Tripo API error: Forbidden (check your API key and permissions).")
                return redirect(url_for('upload'))
            app.logger.error(f"Tripo API error: {str(e)}")
            flash(f'Tripo API error: {str(e)}')
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

    # Step 1: Check if model_url is already set
    if model.model_url:
        app.logger.info(f"Model {model.id} already has model_url: {model.model_url}")
        return jsonify({"status": "SUCCEEDED", "model_url": model.model_url})

    # Step 2: Check GCS for the model file
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(os.environ['BUCKET_NAME'])
        model_filename = f'models/{current_user.id}/{model.id}.glb'
        model_blob = bucket.blob(model_filename)
        if model_blob.exists():
            app.logger.info(f"Model {model.id} found in GCS at {model_filename}")
            try:
                model.model_url = f"https://storage.googleapis.com/{os.environ['BUCKET_NAME']}/{model_filename}"
                db.session.commit()
                app.logger.info(f"Updated model {model.id} with model_url: {model.model_url}")
                return jsonify({"status": "SUCCEEDED", "model_url": model.model_url})
            except Exception as e:
                app.logger.error(f"Failed to update model_url for model {model.id}: {str(e)}")
                db.session.rollback()
                return jsonify({"status": "ERROR", "error": "Failed to update model URL"}), 500
        else:
            app.logger.info(f"Model {model.id} not found in GCS at {model_filename}")
    except Exception as e:
        app.logger.error(f"Error checking GCS for model {model.id}: {str(e)}")
        return jsonify({"status": "ERROR", "error": "Failed to check GCS: " + str(e)}), 500

    # Step 3: If not in GCS, check Tripo API
    if not model.task_id:
        app.logger.error(f"No task_id for model {model.id}")
        return jsonify({"status": "ERROR", "error": "No task ID available"}), 500

    try:
        app.logger.info(f"Checking Tripo API for task_id: {model.task_id}")
        task_response = requests.get(f"https://api.tripo3d.ai/v2/openapi/task/{model.task_id}", headers=HEADERS, timeout=15)
        task_response.raise_for_status()
        task_status = task_response.json()
        status = task_status["data"]["status"]
        progress = task_status["data"].get("progress", 0)
        app.logger.info(f"Task {model.task_id} status: {status}, Progress: {progress}%, Response: {task_status}")

        if status == "success":
            result = task_status["data"].get("result")
            if result:
                glb_url = (result.get("model", {}).get("url") or 
                          result.get("pbr_model", {}).get("url"))
                if glb_url:
                    glb_response = requests.get(glb_url, timeout=15)
                    glb_response.raise_for_status()
                    model_content = glb_response.content
                    model_blob.upload_from_string(model_content, content_type='model/gltf-binary')
                    model.model_url = f"https://storage.googleapis.com/{os.environ['BUCKET_NAME']}/{model_filename}"
                    db.session.commit()
                    app.logger.info(f"Model {model.id} uploaded to {model.model_url}")
                    return jsonify({"status": "SUCCEEDED", "model_url": model.model_url})
                else:
                    app.logger.error(f"Task succeeded but no valid model URL in response: {task_status}")
                    return jsonify({"status": "FAILED", "error": "No GLB URL in response"})
            else:
                app.logger.error(f"Task succeeded but no 'result' in response: {task_status}")
                return jsonify({"status": "FAILED", "error": "No result in response"})
        elif status == "running":
            return jsonify({"status": "IN_PROGRESS", "progress": progress})
        else:
            failure_reason = task_status["data"].get("message", "No failure reason provided")
            app.logger.error(f"Task failed or canceled: {status}, Reason: {failure_reason}")
            return jsonify({"status": status, "error": failure_reason})
    except requests.RequestException as e:
        app.logger.error(f"Status check error: {str(e)}, Task ID: {model.task_id}")
        if model_blob.exists():
            app.logger.info(f"Model {model.id} found in GCS after Tripo error at {model_filename}")
            try:
                model.model_url = f"https://storage.googleapis.com/{os.environ['BUCKET_NAME']}/{model_filename}"
                db.session.commit()
                app.logger.info(f"Updated model {model.id} with model_url: {model.model_url}")
                return jsonify({"status": "SUCCEEDED", "model_url": model.model_url})
            except Exception as e:
                app.logger.error(f"Failed to update model_url for model {model.id}: {str(e)}")
                db.session.rollback()
                return jsonify({"status": "ERROR", "error": "Failed to update model URL after Tripo error"}), 500
        return jsonify({"status": "ERROR", "error": "Tripo API error: " + str(e)}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in status: {str(e)}, Task ID: {model.task_id}")
        return jsonify({"status": "ERROR", "error": "Unexpected error: " + str(e)}), 500

@app.route('/delete_model/<int:model_id>', methods=['POST'])
@login_required
def delete_model(model_id):
    model = Model.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    # Remove model file from GCS if exists
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(os.environ['BUCKET_NAME'])
        # Remove image
        if model.image_url:
            image_path = '/'.join(model.image_url.split('/')[-3:])
            image_blob = bucket.blob(image_path)
            if image_blob.exists():
                image_blob.delete()
        # Remove model file
        if model.model_url:
            model_path = '/'.join(model.model_url.split('/')[-3:])
            model_blob = bucket.blob(model_path)
            if model_blob.exists():
                model_blob.delete()
    except Exception as e:
        app.logger.error(f"Error deleting files from GCS: {str(e)}")
    # Remove from DB
    db.session.delete(model)
    db.session.commit()
    flash('Model deleted successfully.')
    return redirect(url_for('models'))

@app.route('/rename_model/<int:model_id>', methods=['POST'])
@login_required
def rename_model(model_id):
    model = Model.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    new_name = request.form.get('name', '').strip()
    if new_name:
        model.name = new_name
        db.session.commit()
        flash('Model renamed successfully.')
    return redirect(url_for('models'))

@app.route('/admin_rename_model/<int:model_id>', methods=['POST'])
@login_required
def admin_rename_model(model_id):
    if not current_user.is_admin:
        abort(403)
    model = Model.query.get_or_404(model_id)
    new_name = request.form.get('name', '').strip()
    if new_name:
        model.name = new_name
        db.session.commit()
        flash('Model renamed successfully.')
    return redirect(url_for('admin_panel'))

@app.route('/admin_delete_model/<int:model_id>', methods=['POST'])
@login_required
def admin_delete_model(model_id):
    if not current_user.is_admin:
        abort(403)
    model = Model.query.get_or_404(model_id)
    # Remove model file from GCS if exists
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(os.environ['BUCKET_NAME'])
        # Remove image
        if model.image_url:
            image_path = '/'.join(model.image_url.split('/')[-3:])
            image_blob = bucket.blob(image_path)
            if image_blob.exists():
                image_blob.delete()
        # Remove model file
        if model.model_url:
            model_path = '/'.join(model.model_url.split('/')[-3:])
            model_blob = bucket.blob(model_path)
            if model_blob.exists():
                model_blob.delete()
    except Exception as e:
        app.logger.error(f"Error deleting files from GCS: {str(e)}")
    # Remove from DB
    db.session.delete(model)
    db.session.commit()
    flash('Model deleted successfully.')
    return redirect(url_for('admin_panel'))

@app.route('/models', methods=['GET'])
@login_required
def models():
    user_models = Model.query.filter_by(user_id=current_user.id).order_by(Model.created_at.desc()).all()
    app.logger.info(f"Found {len(user_models)} models for user {current_user.id}")
    return render_template('models.html', models=user_models)

@app.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Access denied. Admins only.')
        return redirect(url_for('index'))
    users = User.query.all()
    models = Model.query.all()
    model_details = [
        {
            'id': model.id,
            'user_id': model.user_id,
            'username': User.query.get(model.user_id).username if User.query.get(model.user_id) else 'Deleted User',
            'image_url': model.image_url,
            'model_url': model.model_url,
            'task_id': model.task_id,
            'name': model.name
        }
        for model in models
    ]
    return render_template('admin_panel.html', users=users, models=model_details)

# API for Unity
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'success': True, 'user_id': user.id, 'is_admin': user.is_admin})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'success': True, 'user_id': user.id, 'is_admin': user.is_admin})

@app.route('/api/models', methods=['GET'])
@login_required
def api_get_models():
    models = Model.query.filter_by(user_id=current_user.id).all()
    model_list = [{'id': m.id, 'image_url': m.image_url, 'model_url': m.model_url} for m in models]
    return jsonify({'success': True, 'models': model_list})

# Initialize database
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
    else:
        admin.is_admin = True
        admin.set_password('admin123')
    db.session.commit()
    app.logger.info("Admin user 'admin' ensured with password 'admin123'")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)