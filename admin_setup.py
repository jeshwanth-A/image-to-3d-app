"""
Admin setup script - creates the admin user (mvsr) automatically
"""
import os
import sys
import logging
import traceback
import time
from werkzeug.security import generate_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_url():
    """Get database URL from environment or Secret Manager."""
    # First, try direct environment variable
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        try:
            # Try to import our Secret Manager helper if available
            from secrets import get_secret_or_env
            database_url = get_secret_or_env('database-url', 'DATABASE_URL', 'sqlite:///default.db')
        except ImportError:
            logger.warning("Could not import secrets module, using default database")
            database_url = 'sqlite:///default.db'
    
    # Log which database we're using (without credentials)
    if database_url.startswith('sqlite://'):
        logger.info(f"Using SQLite database: {database_url}")
    else:
        # Parse the URL to hide credentials
        parts = database_url.split('://')
        if len(parts) == 2:
            protocol = parts[0]
            rest = parts[1].split('@')
            if len(rest) == 2:
                host_part = rest[1]
                logger.info(f"Using {protocol} database at {host_part.split('/')[0]}")
            else:
                logger.info(f"Using {protocol} database")
    
    # Handle PostgreSQL URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return database_url

def setup_admin_user():
    """Set up the admin user directly."""
    try:
        # Get database URL
        database_url = get_db_url()
        
        # Create a minimal Flask app
        app = Flask(__name__)
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
        
        # Wait for database to be available (useful for containers)
        max_retries = 5
        retry_count = 0
        connected = False
        
        logger.info("Attempting to connect to database...")
        while not connected and retry_count < max_retries:
            try:
                with app.app_context():
                    db.engine.connect()
                    connected = True
                    logger.info("Successfully connected to database.")
            except Exception as e:
                retry_count += 1
                wait_time = retry_count * 2
                logger.warning(f"Database connection failed (attempt {retry_count}/{max_retries}): {e}")
                logger.info(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
        
        if not connected:
            logger.error("Failed to connect to database after multiple attempts.")
            return False
            
        # Create tables if they don't exist
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created (if they didn't exist)")
            except Exception as e:
                logger.error(f"Error creating tables: {e}")
                return False
        
        # Now create or update the admin user
        with app.app_context():
            try:
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
                db.session.rollback()
                logger.error(f"Error setting up admin user: {e}")
                logger.error(traceback.format_exc())
                return False
                
    except Exception as e:
        logger.error(f"Error in setup_admin_user: {e}")
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
        # Exit with error code but don't prevent container from starting
        sys.exit(0)
