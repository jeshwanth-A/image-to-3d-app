import os
import sys
from flask import Flask, jsonify, request, redirect, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import logging
import pytz
import traceback

# Import our Secret Manager helper (changed from 'secrets' to 'gcp_secrets')
from gcp_secrets import get_secret_or_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Get configuration from Secret Manager
DATABASE_URL = get_secret_or_env('database-url', 'DATABASE_URL', 'sqlite:///default.db')
FLASK_SECRET_KEY = get_secret_or_env('flask-secret-key', 'FLASK_SECRET_KEY', 'default_secret_key')

# Handle PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Debug mode based on environment variable
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']

# Log configuration status
logger.info(f"Database URL configured: {'valid' if DATABASE_URL != 'sqlite:///default.db' else 'using default'}")
logger.info(f"Secret key configured: {'valid' if FLASK_SECRET_KEY != 'default_secret_key' else 'using default'}")

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import models
from models import db, User, Upload

# Initialize database with the app
db.init_app(app)

# Create all tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None

# Add error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    logger.error(traceback.format_exc())
    return jsonify({
        "error": "Internal Server Error",
        "details": str(error) if app.config.get('DEBUG', False) else None,
        "request_path": request.path,
        "request_method": request.method,
    }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "path": request.path,
        "method": request.method
    }), 404

# Log all requests
@app.before_request
def log_request():
    logger.info(f"Request: {request.method} {request.path}")

# Import and register routes blueprint first (for health checks)
try:
    from routes import routes_bp
    app.register_blueprint(routes_bp)
    logger.info("Routes blueprint registered successfully")
except Exception as e:
    logger.error(f"Error registering routes blueprint: {e}")
    logger.error(traceback.format_exc())

# Import other blueprints after models are defined
try:
    # Try importing the blueprints
    try:
        from auth import auth_bp
        app.register_blueprint(auth_bp)
        logger.info("Auth blueprint registered successfully")
    except Exception as e:
        logger.error(f"Error registering auth blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from upload import upload_bp
        app.register_blueprint(upload_bp)
        logger.info("Upload blueprint registered successfully")
    except Exception as e:
        logger.error(f"Error registering upload blueprint: {e}")
        logger.error(traceback.format_exc())
    
except Exception as e:
    logger.error(f"Error registering blueprints: {e}")
    logger.error(traceback.format_exc())

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
                    try:
                        from upload import check_task_status
                        check_task_status()
                        logger.info("Check task status completed successfully")
                    except Exception as e:
                        logger.error(f"Error in check_task_status: {e}")
                        logger.error(traceback.format_exc())
            except Exception as e:
                logger.error(f"Error checking tasks: {e}")
                logger.error(traceback.format_exc())
        
        scheduler.add_job(check_tasks, 'interval', minutes=5)
        return scheduler
    except Exception as e:
        logger.error(f"Failed to set up scheduler: {e}")
        logger.error(traceback.format_exc())
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
        app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
else:
    # For gunicorn environment
    try:
        # Initialize but don't start scheduler - will be handled by the worker processes
        logger.info("Initializing Flask app for gunicorn...")
    except Exception as e:
        logger.error(f"Error initializing app for gunicorn: {e}")
        logger.error(traceback.format_exc())

# Keep all existing code, just add this additional route to catch the signup error:

@app.route('/signup', methods=['GET', 'POST'])
def signup_redirect():
    """Redirect /signup to /auth/signup"""
    return redirect(url_for('auth.signup'))