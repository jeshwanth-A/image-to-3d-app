from flask import Blueprint, request, flash, redirect, url_for, render_template_string, current_app, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
import logging
import traceback

from main import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)

# Simple login form template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #333; }
        form { background-color: #f9f9f9; padding: 20px; border-radius: 5px; max-width: 400px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; border-radius: 4px; }
        .error { color: #cc0000; margin-bottom: 15px; }
        .success { color: #4CAF50; margin-bottom: 15px; }
        .links { margin-top: 15px; }
        .links a { margin-right: 15px; }
    </style>
</head>
<body>
    <h1>Login</h1>
    
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    
    {% if message %}
    <div class="success">{{ message }}</div>
    {% endif %}
    
    <form method="POST" action="{{ url_for('auth.login') }}">
        <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit">Log In</button>
    </form>
    
    <div class="links">
        <a href="{{ url_for('auth.signup') }}">Sign Up</a>
        <a href="{{ url_for('routes.index') }}">Home</a>
    </div>
</body>
</html>
"""

# Simple signup form template
SIGNUP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sign Up</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #333; }
        form { background-color: #f9f9f9; padding: 20px; border-radius: 5px; max-width: 400px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], input[type="email"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; border-radius: 4px; }
        .error { color: #cc0000; margin-bottom: 15px; }
        .links { margin-top: 15px; }
        .links a { margin-right: 15px; }
    </style>
</head>
<body>
    <h1>Sign Up</h1>
    
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    
    <form method="POST" action="{{ url_for('auth.signup') }}">
        <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" required>
        </div>
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit">Sign Up</button>
    </form>
    
    <div class="links">
        <a href="{{ url_for('auth.login') }}">Login</a>
        <a href="{{ url_for('routes.index') }}">Home</a>
    </div>
</body>
</html>
"""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    message = None
    
    try:
        # Handle form submission
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Check for test credentials (mvsr/mvsr)
            if username == 'mvsr' and password == 'mvsr':
                # Create user if it doesn't exist
                user = User.query.filter_by(username='mvsr').first()
                if not user:
                    # Create the test user
                    try:
                        user = User(
                            username='mvsr',
                            email='mvsr@example.com',
                            password=generate_password_hash('mvsr', method='sha256')
                        )
                        db.session.add(user)
                        db.session.commit()
                        logger.info("Created test user 'mvsr'")
                    except Exception as e:
                        logger.error(f"Error creating test user: {e}")
                        db.session.rollback()
                
                # Get the user again in case creation failed
                user = User.query.filter_by(username='mvsr').first()
                if user:
                    login_user(user)
                    logger.info(f"User {username} logged in with test credentials")
                    return redirect(url_for('routes.index'))
                else:
                    error = "Failed to create test user. Please try again."
            else:
                # Regular login
                user = User.query.filter_by(username=username).first()
                
                if not user or not check_password_hash(user.password, password):
                    error = "Invalid username or password. Try again."
                else:
                    login_user(user)
                    logger.info(f"User {username} logged in")
                    return redirect(url_for('routes.index'))
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        logger.error(traceback.format_exc())
        error = "An error occurred during login. Please try again."
    
    # For GET requests or if login failed
    return render_template_string(LOGIN_TEMPLATE, error=error, message=message)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    
    try:
        if request.method == 'POST':
            # Get form data
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Validate data
            if not username or not email or not password:
                error = "All fields are required."
            elif len(password) < 3:
                error = "Password must be at least 3 characters."
            else:
                # Check if username or email already exists
                existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
                
                if existing_user:
                    error = "Username or email already exists."
                else:
                    try:
                        # Create new user
                        new_user = User(
                            username=username,
                            email=email,
                            password=generate_password_hash(password, method='sha256')
                        )
                        
                        # Add to database
                        db.session.add(new_user)
                        db.session.commit()
                        
                        # Log success and redirect to login
                        logger.info(f"New user created: {username}")
                        return redirect(url_for('auth.login', message="Account created successfully! Please log in."))
                    
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error during user creation: {e}")
                        logger.error(traceback.format_exc())
                        error = "Database error. Please try again."
    
    except Exception as e:
        logger.error(f"Signup error: {e}")
        logger.error(traceback.format_exc())
        error = "An error occurred during signup. Please try again."
    
    # For GET requests or if signup failed
    return render_template_string(SIGNUP_TEMPLATE, error=error)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

# API version for signup (for testing)
@auth_bp.route('/api/signup', methods=['POST'])
def api_signup():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validate data
        if not username or not email or not password:
            return jsonify({"error": "All fields are required"}), 400
            
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            return jsonify({"error": "Username or email already exists"}), 409
            
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method='sha256')
        )
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": "User created successfully"}), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"API signup error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500