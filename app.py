"""
Main application file for the Image-to-3D app.
This simplified version focuses on core functionality.
"""
import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, current_user
from models import db, User, Upload
from gcp_secrets import get_secret_or_env
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get configuration from Secret Manager
    database_url = get_secret_or_env('database-url', 'DATABASE_URL', 'sqlite:///app.db')
    flask_secret_key = get_secret_or_env('flask-secret-key', 'FLASK_SECRET_KEY', 'default_secret_key')
    
    # Handle PostgreSQL URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SECRET_KEY'] = flask_secret_key
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create all tables in the database
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='mvsr').first()
        if not admin:
            admin = User(
                username='mvsr', 
                email='mvsr@example.com',
                password=generate_password_hash('mvsr'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created")
    
    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from admin import admin_bp
    app.register_blueprint(admin_bp)
    
    # Root route redirects to login or admin
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('auth.profile'))
        return redirect(url_for('auth.login'))
    
    # Add error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error=str(e), code=404), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Server error: {str(e)}")
        if request.path.startswith('/auth'):
            if request.is_xhr or request.path.endswith('.json'):
                return jsonify({
                    'error': 'Internal Server Error', 
                    'details': str(e), 
                    'request_path': request.path,
                    'request_method': request.method
                }), 500
        return render_template('error.html', error=str(e), code=500), 500
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
