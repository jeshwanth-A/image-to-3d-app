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
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Check connection health
    'pool_timeout': 30,     # Avoid long waits
}

# Initialize database lazily
db = SQLAlchemy()

def init_app():
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', is_admin=True)
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))
                db.session.add(admin)
                db.session.commit()
                logger.info("Admin user created")
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database init failed: {str(e)}")
            logger.error(traceback.format_exc())

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
            logger.error(f"Signup error: {str(e)}")
            flash('An error occurred during signup.')
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
                timeout=10
            )
            model_url = None
            if response.status_code == 200:
                model_data = response.json()
                model_url = model_data.get('model_url')
                if model_url:
                    model_blob = bucket.blob(f'models/{current_user.id}/{form.image.data.filename}.glb')
                    model_response = requests.get(model_url, timeout=10)
                    model_blob.upload_from_string(model_response.content)
                    model_url = model_blob.public_url
            else:
                logger.warning(f"Meshy API failed: {response.status_code} - {response.text}")

            model = Model(user_id=current_user.id, image_url=image_url, model_url=model_url)
            db.session.add(model)
            db.session.commit()
            flash('Image uploaded successfully!')
            return redirect(url_for('models'))
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            flash('Upload failed.')
    return render_template('upload.html', form=form)

@app.route('/models')
@login_required
def models():
    user_models = Model.query.filter_by(user_id=current_user.id).all()
    return render_template('models.html', models=user_models)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin.html', users=users)

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"500 error: {str(error)}")
    return "Internal Server Error", 500

@app.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return 'OK', 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return 'Database unavailable', 503

# Initialize app
init_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port)