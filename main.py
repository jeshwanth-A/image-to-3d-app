import os
import sys
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import logging
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
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
    # Define models here
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
    app.register_blueprint(auth_bp)
    
    from upload import upload_bp
    app.register_blueprint(upload_bp)
    
    logger.info("Blueprints registered successfully")
except Exception as e:
    logger.error(f"Error registering blueprints: {e}")

# Background job setup
def setup_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.jobstores.memory import MemoryJobStore
        from apscheduler.executors.pool import ThreadPoolExecutor
        
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.UTC
        )
        
        # Background job to check Meshy task statuses
        def check_tasks():
            try:
                with app.app_context():
                    from upload import check_task_status
                    check_task_status()
            except Exception as e:
                logger.error(f"Error checking tasks: {e}")
        
        scheduler.add_job(check_tasks, 'interval', minutes=5)
        return scheduler
    except Exception as e:
        logger.error(f"Failed to set up scheduler: {e}")
        return None

# Only use scheduler when running directly (not with gunicorn)
scheduler = None
if __name__ == '__main__':
    try:
        scheduler = setup_scheduler()
        if scheduler:
            scheduler.start()
        
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Starting Flask on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
else:
    # For gunicorn environment
    try:
        # Initialize but don't start scheduler - will be handled by the worker processes
        logger.info("Initializing Flask app for gunicorn...")
        # If needed, put gunicorn-specific configuration here
    except Exception as e:
        logger.error(f"Error initializing app for gunicorn: {e}")