import logging
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
    password_hash = db.Column(db.String(256), nullable=False)  # Increased to 256

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
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            app.logger.info(f"User {form.username.data} logged in")
            return redirect(url_for('upload'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        image_file = form.image.data
        image_bytes = image_file.read()
        data_uri = image_to_data_uri(image_bytes, image_file.mimetype)
        # Placeholder for Meshy API call
        app.logger.info("Image uploaded; processing with Meshy API would occur here")
        # Example: store in database
        model = Model(user_id=current_user.id, image_url=data_uri)
        db.session.add(model)
        db.session.commit()
        flash('Image uploaded successfully!')
        return redirect(url_for('models'))
    return render_template('upload.html', form=form)

@app.route('/models')
@login_required
def models():
    user_models = Model.query.filter_by(user_id=current_user.id).all()
    return render_template('models.html', models=user_models)

# Initialize database
with app.app_context():
    app.logger.info("Creating database tables...")
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)