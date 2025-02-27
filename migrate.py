"""
Database migration script for creating/updating tables.
Run this manually to ensure tables are properly created.
"""
import os
import sys
import logging
from flask import Flask
from models import db, User, Upload
from gcp_secrets import get_secret_or_env

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations to create/update tables."""
    try:
        # Get database URL from Secret Manager or environment
        database_url = get_secret_or_env('database-url', 'DATABASE_URL')
        if not database_url:
            logger.error("No database URL found")
            return False
            
        # Handle PostgreSQL URL format
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            
        # Log which database we're using (without credentials)
        db_type = database_url.split('://')[0]
        logger.info(f"Running migrations on {db_type} database")
        
        # Create a minimal Flask app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize database with the app
        db.init_app(app)
        
        # Create all tables
        with app.app_context():
            db.create_all()
            logger.info("Tables created successfully:")
            
            # Check which tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            for table in inspector.get_table_names():
                logger.info(f"  - {table}")
                
            return True
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting database migrations...")
    if run_migrations():
        logger.info("Migrations completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed")
        sys.exit(1)
