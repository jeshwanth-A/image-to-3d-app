"""
Admin setup script - creates the admin user (mvsr) automatically
"""
import os
import sys
import logging
import traceback
from werkzeug.security import generate_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from secrets import get_secret_or_env

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_admin_user():
    """Set up the admin user directly."""
    try:
        # Create a minimal Flask app
        app = Flask(__name__)
        
        # Get database URL from Secret Manager or environment variable
        database_url = get_secret_or_env('database-url', 'DATABASE_URL', 'sqlite:///default.db')
        
        # Handle PostgreSQL URL format
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            
        # Configure the database
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy
        db = SQLAlchemy(app)
        
        # Define User model for this script
        class User(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            email = db.Column(db.String(120), unique=True, nullable=False)
            password = db.Column(db.String(200), nullable=False)
            
            def __repr__(self):
                return f'<User {self.username}>'
        
        # Create tables if they don't exist
        with app.app_context():
            db.create_all()
            logger.info("Database tables created (if they didn't exist)")
        
        # Now create or update the admin user
        with app.app_context():
            # Check if admin user exists
            admin_user = User.query.filter_by(username='mvsr').first()
            
            if admin_user:
                logger.info("Admin user 'mvsr' already exists. Updating password.")
                admin_user.password = generate_password_hash('mvsr', method='sha256')
            else:
                logger.info("Creating new admin user 'mvsr'")
                admin_user = User(
                    username='mvsr',
                    email='mvsr@example.com',
                    password=generate_password_hash('mvsr', method='sha256')
                )
                db.session.add(admin_user)
                
            # Commit the changes
            db.session.commit()
            logger.info("Admin user setup completed successfully!")
            
    except Exception as e:
        logger.error(f"Error setting up admin user: {e}")
        logger.error(traceback.format_exc())
        return False
        
    return True

if __name__ == "__main__":
    print("Starting admin user setup...")
    success = setup_admin_user()
    if success:
        print("✅ Admin user 'mvsr' created/updated successfully!")
        print("   Username: mvsr")
        print("   Password: mvsr")
    else:
        print("❌ Failed to set up admin user. See error logs for details.")
        # Don't exit with error code - we want the container to continue starting up
