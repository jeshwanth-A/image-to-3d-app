from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import json
from datetime import datetime
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a random secret key

# Data store (in a real app, you'd use a database)
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# Initialize with admin user if file doesn't exist
if not os.path.exists(USERS_FILE):
    initial_users = [
        {
            "username": "mvsr",
            "email": "admin@example.com",
            "password": "admin123",
            "created_at": datetime.now().isoformat(),
            "is_admin": True
        }
    ]
    save_users(initial_users)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Admin decorator
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
    return render_template('admin.html')

@app.route('/dashboard')
def dashboard():
    return "Welcome to your dashboard!"

# API routes
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400
    
    users = load_users()
    
    # Check if username already exists
    for user in users:
        if user['username'] == username:
            return jsonify({"message": "Username already exists"}), 400
    
    # Add new user
    new_user = {
        "username": username,
        "email": email,
        "password": password,  # In a real app, hash this password!
        "created_at": datetime.now().isoformat(),
        "is_admin": False
    }
    
    users.append(new_user)
    save_users(users)
    
    return jsonify({"message": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    
    users = load_users()
    
    for user in users:
        if user['username'] == username and user['password'] == password:
            session['username'] = username
            is_admin = user.get('is_admin', False)
            return jsonify({"message": "Login successful", "is_admin": is_admin}), 200
    
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
    return jsonify(users), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
