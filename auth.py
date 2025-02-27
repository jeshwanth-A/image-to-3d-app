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
</head>fsfd
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

# Admin panel template to view all users
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - User Management</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        table, th, td { border: 1px solid #ddd; }
        th, td { padding: 10px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .action-button { padding: 5px 10px; margin-right: 5px; background-color: #4CAF50; 
                        color: white; border: none; cursor: pointer; border-radius: 3px; }
        .delete-button { background-color: #f44336; }
        .back-link { margin: 20px 0; }
        .back-link a { padding: 10px; background-color: #4CAF50; color: white; 
                      text-decoration: none; border-radius: 4px; }
        .admin-warning { background-color: #fff3cd; border-left: 4px solid #ffc107; 
                       padding: 10px; margin: 20px 0; }
        .password-field { 
            font-family: monospace;
            background-color: #f8f8f8;
            padding: 3px;
            border: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <h1>Admin Panel - User Management</h1>
    
    <div class="back-link">
        <a href="/">Back to Home</a>
    </div>
    
    <div class="admin-warning">
        <strong>Admin Access:</strong> This page shows sensitive information and is restricted to administrators only.
    </div>
    
    <h2>Registered Users</h2>
    
    <table>
        <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Email</th>
            <th>Password Hash</th>
            <th>Actions</th>
        </tr>
        {% for user in users %}
        <tr>
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td class="password-field">{{ user.password }}</td>
            <td>
                <button class="action-button delete-button" onclick="deleteUser({{ user.id }})">Delete</button>
            </td>
        </tr>
        {% endfor %}
    </table>
    
    <script>
        function deleteUser(userId) {
            if (confirm('Are you sure you want to delete this user?')) {
                fetch('/auth/admin/delete-user/' + userId, { 
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('User deleted successfully');
                        location.reload();
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('An error occurred: ' + error);
                });
            }
        }
    </script>
</body>
</html>
"""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    message = None
    
    # Check if request includes a message parameter (for redirects)
    if request.args.get('message'):
        message = request.args.get('message')
    
    try:
        # Handle form submission
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Check for test credentials (mvsr/mvsr)
            if username == 'mvsr' and password == 'mvsr':
                # Get the user
                user = User.query.filter_by(username='mvsr').first()
                
                if user:
                    # Admin user found, just log them in
                    login_user(user)
                    logger.info(f"Admin user {username} logged in")
                    return redirect(url_for('routes.index'))
                else:
                    # EMERGENCY FIX: Create the admin user if it doesn't exist
                    try:
                        logger.warning("Admin user not found, creating it on the fly...")
                        user = User(
                            username='mvsr',
                            email='mvsr@example.com',
                            password=generate_password_hash('mvsr', method='sha256')
                        )
                        db.session.add(user)
                        db.session.commit()
                        logger.info("Admin user created successfully during login")
                        
                        # Log them in
                        login_user(user)
                        logger.info("Admin user logged in after creation")
                        return redirect(url_for('routes.index'))
                    except Exception as create_err:
                        logger.error(f"Failed to create admin user on the fly: {create_err}")
                        error = f"Failed to create admin user: {str(create_err)}"
            else:
                # Regular login
                user = User.query.filter_by(username=username).first()
                
                if not user:
                    error = "Invalid username. Please try again."
                    logger.warning(f"Login attempt with invalid username: {username}")
                elif not check_password_hash(user.password, password):
                    error = "Invalid password. Please try again."
                    logger.warning(f"Login attempt with invalid password for user: {username}")
                else:
                    login_user(user)
                    logger.info(f"User {username} logged in successfully")
                    return redirect(url_for('routes.index'))
    
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        error = f"Database error: {str(e)}. Please try again."
    
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

# New admin route to view all users
@auth_bp.route('/admin')
@login_required
def admin_panel():
    # Only allow access to user with username 'mvsr'
    if current_user.username != 'mvsr':
        return "Access denied. Admin privileges required.", 403
        
    try:
        # Get all users from database
        users = User.query.all()
        return render_template_string(ADMIN_TEMPLATE, users=users)
    except Exception as e:
        logger.error(f"Error in admin panel: {e}")
        return f"Error loading admin panel: {str(e)}", 500

# Admin route to delete users
@auth_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Only allow access to user with username 'mvsr'
    if current_user.username != 'mvsr':
        return jsonify({"success": False, "error": "Access denied"}), 403
    
    try:
        # Don't allow deleting the admin user
        if user_id == current_user.id:
            return jsonify({"success": False, "error": "Cannot delete admin user"}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"success": True, "message": f"User {user.username} deleted"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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