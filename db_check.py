"""
Database check utility - helps diagnose database connection issues
"""
import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_url():
    """Get database URL from environment or try to import from secrets."""
    # First, try direct environment variable
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        try:
            from secrets import get_secret_or_env
            database_url = get_secret_or_env('database-url', 'DATABASE_URL', 'sqlite:///default.db')
        except ImportError:
            logger.warning("Could not import secrets module, using default database")
            database_url = 'sqlite:///default.db'
    
    # Handle PostgreSQL URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return database_url

def check_database():
    """Check database connectivity."""
    print("🔍 DATABASE CONNECTIVITY TEST")
    print("============================")
    
    # Get database URL
    database_url = get_db_url()
    
    # Create a minimal Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy
    db = SQLAlchemy(app)
    
    # Try to connect to the database
    with app.app_context():
        try:
            connection = db.engine.connect()
            print("✅ Successfully connected to database!")
            
            # Execute a simple query
            result = connection.execute("SELECT 1").scalar()
            print(f"✅ Query executed successfully. Result: {result}")
            
            # Check if tables exist
            try:
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"✅ Tables found in database: {len(tables)}")
                for table in tables:
                    print(f"  - {table}")
                    
                # If User table exists, check if admin exists
                if 'user' in tables:
                    result = connection.execute("SELECT COUNT(*) FROM user WHERE username = 'mvsr'").scalar()
                    if result > 0:
                        print("✅ Admin user 'mvsr' exists in the database.")
                    else:
                        print("❌ Admin user 'mvsr' DOES NOT exist in the database!")
                else:
                    print("❌ User table not found in database!")
            except Exception as e:
                print(f"❌ Failed to inspect database tables: {e}")
            
            # Close the connection
            connection.close()
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

if __name__ == "__main__":
    success = check_database()
    
    print("\nRECOMMENDATIONS:")
    if success:
        print("✅ Database connection is working properly.")
    else:
        print("❌ Database connection failed. Please check:")
        print("  1. Ensure DATABASE_URL is set correctly in environment or Secret Manager")
        print("  2. Check that your database server is running")
        print("  3. Verify network connectivity to your database")
        print("  4. Check credentials are correct")
        print("  5. Try running `flask db upgrade` if tables are missing")
    
    sys.exit(0 if success else 1)
