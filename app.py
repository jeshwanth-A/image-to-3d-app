from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, EqualTo
import os
from google.cloud import storage
import requests
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # INFO for production, DEBUG for detailed local testing
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
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

# Database initialization
def init_db():
    try:
        db.create_all()
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Admin user created")
        app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Database initialization failed: {str(e)}")

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
            app.logger.error(f"Signup error: {str(e)}")
            flash('An error occurred during signup. Please try again.')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}")
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
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
            storage_client = storage.Client()
            bucket = storage_client.bucket(os.environ['BUCKET_NAME'])
            filename = f'images/{current_user.id}/{form.image.data.filename}'
            blob = bucket.blob(filename)
            blob.upload_from_file(form.image.data)
            image_url = blob.public_url

            meshy_api_key = os.environ['MESHY_API_KEY']
            response = requests.post(
                'https://api.meshy.ai/v1/models',
                headers={'Authorization': f'Bearer {meshy_api_key}'},
                json={'image_url': image_url},
                timeout=30  # Avoid hanging on slow API responses
            )
            model_url = None
            if response.status_code == 200:
                model_data = response.json()
                model_url = model_data.get('model_url')
                if model_url:
                    model_blob = bucket.blob(f'models/{current_user.id}/{form.image.data.filename}.glb')
                    model_response = requests.get(model_url, timeout=30)
                    model_blob.upload_from_string(model_response.content)
                    model_url = model_blob.public_url
            else:
                app.logger.error(f"Meshy API failed: {response.status_code} - {response.text}")
                flash('Failed to generate 3D model.')

            model = Model(user_id=current_user.id, image_url=image_url, model_url=model_url)
            db.session.add(model)
            db.session.commit()
            flash('Image uploaded and model generated!')
            return redirect(url_for('models'))
        except Exception as e:
            app.logger.error(f"Upload error: {str(e)}")
            flash('An error occurred during upload.')
    return render_template('upload.html', form=form)

@app.route('/models')
@login_required
def models():
    try:
        user_models = Model.query.filter_by(user_id=current_user.id).all()
        return render_template('models.html', models=user_models)
    except Exception as e:
        app.logger.error(f"Models route error: {str(e)}")
        flash('An error occurred while loading models.')
        return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    try:
        users = User.query.all()
        return render_template('admin.html', users=users)
    except Exception as e:
        app.logger.error(f"Admin route error: {str(e)}")
        flash('An error occurred in admin panel.')
        return redirect(url_for('index'))

# Error Handlers
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f"500 error: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

# Initialize database before first request
@app.before_first_request
def before_first_request():
    with app.app_context():
        init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))