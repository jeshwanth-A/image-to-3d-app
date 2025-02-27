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
    """Handle user login."""
    try:
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('auth.profile'))
            
        error = None
        message = request.args.get('message')
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                error = "Username and password are required"
            else:
                try:
                    user = User.query.filter_by(username=username).first()
                    
                    # Check credentials
                    if user and check_password_hash(user.password, password):
                        login_user(user)
                        logger.info(f"User {username} logged in successfully")
                        
                        if user.is_admin:
                            return redirect(url_for('admin.dashboard'))
                        return redirect(url_for('auth.profile'))
                    else:
                        error = 'Invalid username or password'
                        logger.warning(f"Failed login attempt for username: {username}")
                except Exception as e:
                    logger.error(f"Database error during login: {str(e)}")
                    logger.error(traceback.format_exc())
                    error = "System error occurred during login"
        
        # Use direct template string if login.html doesn't exist
        try:
            return render_template('login.html', error=error, message=message)
        except Exception as template_error:
            logger.warning(f"Could not render login template: {str(template_error)}")
            return render_template_string(LOGIN_TEMPLATE, error=error, message=message)
            
    except Exception as e:
        logger.error(f"Unexpected error in login route: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | 
                                          (User.email == email)).first()
        
        if existing_user:
            flash('Username or email already exists')
        else:
            # Create new user
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                is_admin=(username == 'mvsr')  # Only 'mvsr' is admin
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully!')
            return redirect(url_for('auth.login'))
    
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html')