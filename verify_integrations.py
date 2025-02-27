"""
Verification script to check if all cloud services are working together.
Run this locally to verify database, bucket, and Secret Manager.
"""
import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import traceback
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceChecker:
    """Class to check various cloud services."""
    
    def __init__(self):
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "database": {"status": "untested"},
            "secrets": {"status": "untested"},
            "storage": {"status": "untested"}
        }
    
    def check_all(self):
        """Run all checks."""
        print("🔍 CLOUD SERVICES INTEGRATION TEST")
        print("==================================")
        print(f"Project ID: {self.project_id or 'Not set in environment'}")
        print("")
        
        self.check_secrets()
        self.check_database()
        self.check_storage()
        
        # Print a summary
        print("\n📋 TEST SUMMARY")
        print("==============")
        
        for service, result in self.results.items():
            if service == "timestamp":
                continue
                
            status = result.get("status", "unknown")
            if status == "ok":
                icon = "✅"
            elif status == "warning":
                icon = "⚠️"
            elif status == "error":
                icon = "❌"
            else:
                icon = "❓"
                
            print(f"{icon} {service.capitalize()}: {status}")
            if status != "ok" and result.get("message"):
                print(f"   → {result['message']}")
        
        # Give recommendations
        self.provide_recommendations()
        
        return self.results
    
    def check_secrets(self):
        """Check if Secret Manager is working."""
        print("📝 Checking Secret Manager...")
        
        try:
            # Try to import our Secret Manager helper (changed name)
            try:
                from gcp_secrets import get_secret_or_env
                secret_module = True
                print("  ✓ gcp_secrets.py module found")
            except ImportError:
                secret_module = False
                print("  ✗ gcp_secrets.py module not found")
                
            # Check if Google Cloud Secret Manager library is installed
            try:
                from google.cloud import secretmanager
                gcp_lib = True
                print("  ✓ Google Cloud Secret Manager library found")
            except ImportError:
                gcp_lib = False
                print("  ✗ Google Cloud Secret Manager library not found")
            
            if not secret_module or not gcp_lib:
                self.results["secrets"] = {
                    "status": "warning",
                    "message": "Required modules not found"
                }
                return
            
            # Try accessing a secret
            secrets_to_check = [
                'database-url',
                'flask-secret-key',
                'meshy-api-key'
            ]
            
            accessed = 0
            for secret_id in secrets_to_check:
                secret_value = get_secret_or_env(secret_id)
                if secret_value:
                    print(f"  ✓ Successfully accessed secret '{secret_id}'")
                    accessed += 1
                else:
                    print(f"  ✗ Could not access secret '{secret_id}'")
            
            if accessed == len(secrets_to_check):
                self.results["secrets"] = {
                    "status": "ok",
                    "message": f"All {accessed} secrets accessed successfully"
                }
            elif accessed > 0:
                self.results["secrets"] = {
                    "status": "warning",
                    "message": f"Only {accessed}/{len(secrets_to_check)} secrets could be accessed"
                }
            else:
                self.results["secrets"] = {
                    "status": "error",
                    "message": "Could not access any secrets"
                }
        
        except Exception as e:
            logger.error(f"Error checking secrets: {e}")
            logger.error(traceback.format_exc())
            self.results["secrets"] = {
                "status": "error",
                "message": str(e)
            }
    
    def check_database(self):
        """Check if database is working."""
        print("\n🗄️ Checking Database...")
        
        try:
            # Get database URL (updated import)
            try:
                from gcp_secrets import get_secret_or_env
                database_url = get_secret_or_env('database-url', 'DATABASE_URL')
                if not database_url:
                    database_url = os.environ.get('DATABASE_URL')
            except ImportError:
                database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                print("  ✗ Database URL not found")
                self.results["database"] = {
                    "status": "error",
                    "message": "Database URL not found"
                }
                return
                
            # Create a minimal Flask app
            app = Flask(__name__)
            
            # Handle PostgreSQL URL format
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
                
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            # Initialize SQLAlchemy
            db = SQLAlchemy(app)
            
            # Try to connect to the database
            with app.app_context():
                connection = db.engine.connect()
                print("  ✓ Successfully connected to database")
                
                # Try a simple query
                result = connection.execute("SELECT 1").scalar()
                print(f"  ✓ Test query successful (result: {result})")
                
                # Check if User table exists
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                
                if 'user' in [t.lower() for t in tables]:
                    print("  ✓ User table found")
                    
                    # Check for admin user
                    try:
                        admin_count = connection.execute(
                            "SELECT COUNT(*) FROM \"user\" WHERE username = 'mvsr'"
                        ).scalar()
                        
                        if admin_count > 0:
                            print("  ✓ Admin user 'mvsr' exists")
                        else:
                            print("  ✗ Admin user 'mvsr' not found")
                    except Exception as e:
                        print(f"  ✗ Error checking for admin user: {e}")
                else:
                    print("  ✗ User table not found")
                
                # Close the connection
                connection.close()
                
                self.results["database"] = {
                    "status": "ok",
                    "message": "Connected successfully",
                    "tables": tables
                }
            
        except Exception as e:
            logger.error(f"Error checking database: {e}")
            logger.error(traceback.format_exc())
            self.results["database"] = {
                "status": "error",
                "message": str(e)
            }
    
    def check_storage(self):
        """Check if Cloud Storage bucket is working."""
        print("\n🪣 Checking Cloud Storage...")
        
        try:
            # Check if Google Cloud Storage library is installed
            try:
                from google.cloud import storage
                print("  ✓ Google Cloud Storage library found")
            except ImportError:
                print("  ✗ Google Cloud Storage library not found")
                self.results["storage"] = {
                    "status": "error",
                    "message": "Google Cloud Storage library not installed"
                }
                return
            
            # Get bucket name
            bucket_name = os.environ.get('GCS_BUCKET_NAME') or os.environ.get('STORAGE_BUCKET')
            if not bucket_name:
                print("  ✗ Bucket name not found in environment variables")
                self.results["storage"] = {
                    "status": "error",
                    "message": "Bucket name not found in environment variables"
                }
                return
            
            print(f"  ✓ Bucket name found: {bucket_name}")
            
            # Try to access the bucket
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                
                # Check if the bucket exists
                if bucket.exists():
                    print(f"  ✓ Bucket '{bucket_name}' exists")
                    
                    # Try listing objects
                    blobs = list(bucket.list_blobs(max_results=5))
                    print(f"  ✓ Listed {len(blobs)} objects in bucket")
                    
                    # Try uploading a test file
                    test_blob = bucket.blob('test-connection.txt')
                    test_blob.upload_from_string(
                        f'Test connection at {datetime.now().isoformat()}', 
                        content_type='text/plain'
                    )
                    print("  ✓ Successfully uploaded test file")
                    
                    # Try downloading the test file
                    content = test_blob.download_as_text()
                    print(f"  ✓ Successfully downloaded test file: {content[:30]}...")
                    
                    # Delete the test file
                    test_blob.delete()
                    print("  ✓ Successfully deleted test file")
                    
                    self.results["storage"] = {
                        "status": "ok",
                        "message": "All operations successful"
                    }
                else:
                    print(f"  ✗ Bucket '{bucket_name}' does not exist")
                    self.results["storage"] = {
                        "status": "error",
                        "message": f"Bucket '{bucket_name}' does not exist"
                    }
            except Exception as e:
                print(f"  ✗ Error accessing bucket: {e}")
                self.results["storage"] = {
                    "status": "error",
                    "message": str(e)
                }
                
        except Exception as e:
            logger.error(f"Error checking storage: {e}")
            logger.error(traceback.format_exc())
            self.results["storage"] = {
                "status": "error",
                "message": str(e)
            }
    
    def provide_recommendations(self):
        """Provide recommendations based on test results."""
        print("\n📋 RECOMMENDATIONS")
        print("================")
        
        # Database recommendations
        db_status = self.results["database"]["status"]
        if db_status == "error":
            print("🗄️ Database:")
            print("  1. Check your DATABASE_URL environment variable or database-url secret")
            print("  2. Ensure your database server is running")
            print("  3. Verify that your service account has access to the database")
            print("  4. Try running admin_setup.py to create the database schema and admin user")
        
        # Secrets recommendations
        secrets_status = self.results["secrets"]["status"]
        if secrets_status != "ok":
            print("📝 Secret Manager:")
            print("  1. Ensure GOOGLE_CLOUD_PROJECT is set in your environment")
            print("  2. Verify that required secrets exist in Secret Manager:")
            print("     - database-url")
            print("     - flask-secret-key")
            print("     - meshy-api-key")
            print("  3. Check that your service account has Secret Manager access")
            print("  4. Run: gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\")
            print("           --member=serviceAccount:YOUR_SERVICE_ACCOUNT \\")
            print("           --role=roles/secretmanager.secretAccessor")
        
        # Storage recommendations
        storage_status = self.results["storage"]["status"]
        if storage_status != "ok":
            print("🪣 Cloud Storage:")
            print("  1. Ensure GCS_BUCKET_NAME or STORAGE_BUCKET is set in your environment")
            print("  2. Verify that your bucket exists")
            print("  3. Check that your service account has Storage Object Admin access")
            print("  4. Run: gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\")
            print("           --member=serviceAccount:YOUR_SERVICE_ACCOUNT \\")
            print("           --role=roles/storage.objectAdmin")
        
        # All good
        if db_status == "ok" and secrets_status == "ok" and storage_status == "ok":
            print("🎉 All systems are working correctly! No action needed.")

if __name__ == "__main__":
    checker = ServiceChecker()
    results = checker.check_all()
    
    # Save results to file
    with open('integration_check_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to integration_check_results.json")
    
    # Exit with appropriate code
    all_ok = all(results[service]["status"] == "ok" for service in ["database", "secrets", "storage"])
    sys.exit(0 if all_ok else 1)
