from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import json
from datetime import datetime
import secrets
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Data store configuration
USERS_FILE = os.environ.get('USERS_FILE', 'users.json')
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_PATH = os.path.join(DATA_DIR, USERS_FILE)

def load_users():
    """Load users from JSON file"""
    try:
        if os.path.exists(USERS_PATH):
            with open(USERS_PATH, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

def save_users(users):
    """Save users to JSON file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
        with open(USERS_PATH, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

# Initialize with admin user if file doesn't exist
if not os.path.exists(USERS_PATH):
    initial_users = [
        {
            "username": "mvsr",
            "email": "admin@example.com",
            "password": generate_password_hash("admin123"),  # Hash the password
            "created_at": datetime.now().isoformat(),
            "is_admin": True
        }
    ]
    save_users(initial_users)

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"message": "Authentication required"}), 401
        
        users = load_users()
        for user in users:
            if user['username'] == session['username'] and user.get('is_admin', False):
                return f(*args, **kwargs)
        
        return jsonify({"message": "Admin privileges required"}), 403
    return decorated_function

# Routes for templates
@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/admin')
def admin_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('admin.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return "Welcome to your dashboard!"

# API routes
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Validate input
    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400
    
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400
    
    users = load_users()
    
    # Check if username already exists
    if any(user['username'] == username for user in users):
        return jsonify({"message": "Username already exists"}), 400
    
    # Add new user with hashed password
    new_user = {
        "username": username,
        "email": email,
        "password": generate_password_hash(password),
        "created_at": datetime.now().isoformat(),
        "is_admin": False
    }
    
    users.append(new_user)
    if save_users(users):
        return jsonify({"message": "User created successfully"}), 201
    else:
        return jsonify({"message": "Failed to create user"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    
    users = load_users()
    
    for user in users:
        if user['username'] == username:
            # First handle old plain text passwords (if any)
            if 'is_hashed' not in user and user['password'] == password:
                # Update to hashed password
                user['password'] = generate_password_hash(password)
                user['is_hashed'] = True
                save_users(users)
                session['username'] = username
                return jsonify({
                    "message": "Login successful",
                    "is_admin": user.get('is_admin', False)
                }), 200
            # Then handle hashed passwords
            elif check_password_hash(user['password'], password):
                session['username'] = username
                return jsonify({
                    "message": "Login successful",
                    "is_admin": user.get('is_admin', False)
                }), 200
            else:
                break  # Username found but wrong password
    
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/check-admin')
@login_required
def check_admin():
    username = session['username']
    users = load_users()
    
    for user in users:
        if user['username'] == username:
            return jsonify({"is_admin": user.get('is_admin', False)}), 200
    
    return jsonify({"is_admin": False}), 404

@app.route('/api/users')
@admin_required
def get_users():
    users = load_users()
    # For security, mask actual passwords in the response
    sanitized_users = []
    for user in users:
        sanitized_user = user.copy()
        sanitized_user['password'] = '********' if user.get('is_admin', False) else user['password']
        sanitized_users.append(sanitized_user)
    return jsonify(sanitized_users), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
