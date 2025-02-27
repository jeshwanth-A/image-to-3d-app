"""Test database and storage connections."""
import os
from google.cloud import storage
from flask import Flask
from models import db, User

# Test database connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Test storage connection
storage_client = storage.Client()
bucket = storage_client.bucket(os.environ.get('GCS_BUCKET_NAME', 'project-2-450420-images'))

print("TESTING CONNECTIONS")
print("===================")

# Test database
with app.app_context():
    try:
        result = db.session.execute("SELECT 1").scalar()
        print(f"✅ Database connection successful: {result}")
        
        # Check for User table
        users = User.query.count()
        print(f"✅ Found {users} users in database")
    except Exception as e:
        print(f"❌ Database error: {e}")

# Test storage
try:
    exists = bucket.exists()
    print(f"✅ Storage bucket exists: {exists}")
    if exists:
        blobs = list(bucket.list_blobs(max_results=5))
        print(f"✅ Found {len(blobs)} objects in bucket")
except Exception as e:
    print(f"❌ Storage bucket error: {e}")