"""
Diagnostics script to check database connectivity and environment setup.
Run this file directly to diagnose issues with your app.
"""
import os
import sys
import logging
import traceback
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from secrets import get_secret_or_env

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database():
    """Check database connectivity."""
    try:
        # Get database URL
        database_url = get_secret_or_env('database-url', 'DATABASE_URL', 'sqlite:///default.db')
        logger.info(f"Using database URL: {'[MASKED]' if database_url != 'sqlite:///default.db' else database_url}")
        
        # Handle PostgreSQL URL format
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            logger.info("Converted postgres:// URL format to postgresql://")
        
        # Create a minimal Flask app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy
        db = SQLAlchemy(app)
        
        # Test database connection
        with app.app_context():
            connection = db.engine.connect()
            connection.execute("SELECT 1")
            connection.close()
            logger.info("✅ Database connection test succeeded!")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        logger.error(traceback.format_exc())
        return False

def check_secrets():
    """Check if secrets can be accessed."""
    secrets_to_check = [
        ('database-url', 'DATABASE_URL'),
        ('flask-secret-key', 'FLASK_SECRET_KEY'),
        ('meshy-api-key', 'MESHY_API_KEY')
    ]
    
    all_success = True
    
    for secret_id, env_var in secrets_to_check:
        try:
            # Try to get the secret
            value = get_secret_or_env(secret_id, env_var)
            
            if value:
                logger.info(f"✅ Successfully accessed '{secret_id}' (or '{env_var}')")
            else:
                logger.warning(f"⚠️ Could not access '{secret_id}' or '{env_var}'")
                all_success = False
        
        except Exception as e:
            logger.error(f"❌ Error accessing secret '{secret_id}': {e}")
            all_success = False
    
    return all_success

def check_environment():
    """Check environment variables."""
    env_vars_to_check = [
        'GOOGLE_CLOUD_PROJECT',
        'PORT',
        'GCS_BUCKET_NAME',
        'STORAGE_BUCKET'
    ]
    
    all_present = True
    
    for var in env_vars_to_check:
        if os.environ.get(var):
            logger.info(f"✅ Environment variable {var} is set")
        else:
            logger.warning(f"⚠️ Environment variable {var} is not set")
            all_present = False
    
    return all_present

if __name__ == "__main__":
    print("Running diagnostics...")
    
    # Check database
    print("\n=== DATABASE CHECK ===")
    db_ok = check_database()
    
    # Check secrets
    print("\n=== SECRETS CHECK ===")
    secrets_ok = check_secrets()
    
    # Check environment
    print("\n=== ENVIRONMENT CHECK ===")
    env_ok = check_environment()
    
    # Print summary
    print("\n=== DIAGNOSTICS SUMMARY ===")
    print(f"Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"Secrets: {'✅ OK' if secrets_ok else '⚠️ ISSUES FOUND'}")
    print(f"Environment: {'✅ OK' if env_ok else '⚠️ ISSUES FOUND'}")
    
    if db_ok and secrets_ok and env_ok:
        print("\n✅ All checks passed! Your environment seems properly configured.")
    else:
        print("\n⚠️ Some checks failed. See logs above for details.")
        if not db_ok:
            print("\n🛠️ To fix database issues:")
            print("  1. Check if your database URL is correctly configured")
            print("  2. Ensure the database server is running and accessible")
            print("  3. Verify permissions for the database user")
        if not secrets_ok:
            print("\n🛠️ To fix secrets issues:")
            print("  1. Verify Secret Manager is configured correctly")
            print("  2. Make sure your service account has Secret Manager access")
            print("  3. Check that all required secrets exist in Secret Manager")
        if not env_ok:
            print("\n🛠️ To fix environment issues:")
            print("  1. Set missing environment variables in your Cloud Run configuration")
