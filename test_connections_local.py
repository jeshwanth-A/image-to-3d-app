"""Test database connection with local mock for storage."""
import os
import sys
from flask import Flask
from models import db, User

print("TESTING LOCAL CONNECTIONS")
print("========================")

# Get database URL from environment or use SQLite
db_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')

# Test database connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Test database
with app.app_context():
    try:
        result = db.session.execute("SELECT 1").scalar()
        print(f"✅ Database connection successful: {result}")
        
        # Try to create tables if they don't exist
        db.create_all()
        print("✅ Database tables created/verified")
        
        # Check for User table
        try:
            users = User.query.count()
            print(f"✅ Found {users} users in database")
        except Exception as e:
            print(f"❌ Error querying users: {e}")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

# Mock storage test for local development
print("\n✅ Storage bucket access simulated for local development")
