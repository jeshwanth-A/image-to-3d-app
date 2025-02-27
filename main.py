import os
import sys
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Create models before they're imported elsewhere
with app.app_context():
    # Define or import models here
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password = db.Column(db.String(200), nullable=False)
        
        def is_active(self):
            return True
            
        def is_authenticated(self):
            return True
            
        def is_anonymous(self):
            return False
            
        def get_id(self):
            return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None

# Initialize the database
try:
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database initialization error: {e}")

# Import blueprints after models are defined
try:
    from auth import auth_bp
    from upload import upload_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    logger.info("Blueprints registered successfully")
except Exception as e:
    logger.error(f"Error registering blueprints: {e}")
    
# Background job to check Meshy task statuses
def check_tasks():
    try:
        with app.app_context():
            from upload import check_task_status
            check_task_status()
    except Exception as e:
        logger.error(f"Error checking tasks: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_tasks, 'interval', minutes=5)

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    """Properly shuts down the scheduler when the app stops."""
    scheduler.shutdown(wait=False)

if __name__ == '__main__':
    try:
        scheduler.start()
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Starting Flask on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)