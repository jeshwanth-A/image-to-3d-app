from flask import Blueprint, jsonify, current_app, render_template_string, url_for
from flask_login import current_user, login_required
import sys
import os
import datetime
import logging
import traceback
from secrets import get_secret_or_env

routes_bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

@routes_bp.route('/')
def index():
    """Main landing page with links to all parts of the application."""
    # Create a simple HTML page with links
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Image to 3D App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; }
            .nav-links { margin: 20px 0; }
            .nav-links a { display: inline-block; margin-right: 15px; padding: 10px; 
                          background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; }
            .status { background-color: #f8f8f8; border-left: 4px solid #4CAF50; padding: 10px; margin: 20px 0; }
            .user-info { background-color: #e9f7ef; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>Image to 3D App</h1>
        <p>The application is running successfully!</p>
        
        {% if is_logged_in %}
        <div class="user-info">
            <strong>Logged in as:</strong> {{ username }}
            <div style="margin-top: 10px;">
                <a href="{{ logout_url }}" style="color: #cc0000; text-decoration: none;">Log Out</a>
            </div>
        </div>
        {% endif %}
        
        <div class="status">
            <strong>Status:</strong> Online
            <br>
            <strong>Time:</strong> {{ current_time }}
        </div>
        
        <h2>Navigation</h2>
        <div class="nav-links">
            {% if not is_logged_in %}
                {% if auth_url %}<a href="{{ auth_url }}">Login/Register</a>{% endif %}
            {% else %}
                {% if upload_url %}<a href="{{ upload_url }}">Upload Images</a>{% endif %}
                <a href="/diagnostics">System Diagnostics</a>
            {% endif %}
        </div>
        
        {% if is_admin %}
        <div style="margin-top: 30px;">
            <h3>Admin Links</h3>
            <div class="nav-links">
                <a href="/auth/admin">User Management</a>
                <a href="/health">Health Status</a>
                <a href="/routes">View All Routes</a>
                <a href="/debug">Debug Information</a>
            </div>
        </div>
        {% endif %}
    </body>
    </html>
    """
    
    # Try to generate URLs for auth and upload
    auth_url = None
    upload_url = None
    logout_url = None
    
    try:
        auth_url = url_for('auth.login')
        logout_url = url_for('auth.logout')
    except Exception as e:
        logger.error(f"Could not generate auth URLs: {e}")
    
    try:
        upload_url = url_for('upload.upload_form')
    except Exception as e:
        logger.error(f"Could not generate upload URL 'upload_form': {e}")
        # Try alternative names
        try:
            upload_url = url_for('upload.index')
        except Exception:
            logger.error(f"Could not generate upload URL 'index': {e}")
    
    # Get username if logged in
    username = None
    if current_user.is_authenticated:
        username = current_user.username
    
    # Check if user is admin (assume username 'mvsr' is admin)
    is_admin = current_user.is_authenticated and username == 'mvsr'
    
    return render_template_string(
        html_template, 
        current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        auth_url=auth_url,
        upload_url=upload_url,
        logout_url=logout_url,
        is_logged_in=current_user.is_authenticated,
        username=username,
        is_admin=is_admin
    )

@routes_bp.route('/health')
def health():
    """Health check endpoint for diagnostics."""
    try:
        return jsonify({
            "status": "ok",
            "timestamp": datetime.datetime.now().isoformat(),
            "python_version": sys.version,
            "environment": {k: v for k, v in os.environ.items() if not k.startswith('_')}
        })
    except Exception as e:
        logger.exception("Error in health check")
        return jsonify({"status": "error", "error": str(e)}), 500

@routes_bp.route('/diagnostics')
@login_required
def diagnostics():
    """Diagnostics page for users to check connections."""
    from main import db
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Diagnostics</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1, h2 { color: #333; }
            .status-box { padding: 15px; margin-bottom: 20px; border-radius: 5px; }
            .status-ok { background-color: #dff0d8; border: 1px solid #d6e9c6; }
            .status-warning { background-color: #fcf8e3; border: 1px solid #faebcc; }
            .status-error { background-color: #f2dede; border: 1px solid #ebccd1; }
            .back-link { margin: 20px 0; }
            .back-link a { padding: 10px; background-color: #4CAF50; color: white; 
                          text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>System Diagnostics</h1>
        
        <div class="back-link">
            <a href="/">Back to Home</a>
        </div>
        
        <h2>Database Connection</h2>
        <div class="status-box {% if db_ok %}status-ok{% else %}status-error{% endif %}">
            <strong>Status:</strong> {% if db_ok %}Connected{% else %}Error{% endif %}
            {% if not db_ok %}<br><strong>Error:</strong> {{ db_error }}{% endif %}
        </div>
        
        <h2>Environment Configuration</h2>
        <div class="status-box {% if has_database_url %}status-ok{% else %}status-warning{% endif %}">
            <strong>DATABASE_URL:</strong> {% if has_database_url %}Configured{% else %}Missing{% endif %}
        </div>
        <div class="status-box {% if has_secret_key %}status-ok{% else %}status-warning{% endif %}">
            <strong>SECRET_KEY:</strong> {% if has_secret_key %}Configured{% else %}Using default{% endif %}
        </div>
        <div class="status-box {% if has_storage_bucket %}status-ok{% else %}status-warning{% endif %}">
            <strong>STORAGE_BUCKET:</strong> {% if has_storage_bucket %}Configured{% else %}Missing{% endif %}
        </div>
        <div class="status-box {% if has_api_key %}status-ok{% else %}status-warning{% endif %}">
            <strong>MESHY_API_KEY:</strong> {% if has_api_key %}Configured{% else %}Missing{% endif %}
        </div>
        
        <h2>Application Status</h2>
        <div class="status-box status-ok">
            <strong>Flask App:</strong> Running
            <br>
            <strong>Debug Mode:</strong> {{ debug_mode }}
            <br>
            <strong>User:</strong> {{ username }}
        </div>
    </body>
    </html>
    """
    
    # Check database connection
    db_ok = False
    db_error = None
    try:
        db.session.execute("SELECT 1")
        db_ok = True
    except Exception as e:
        db_error = str(e)
    
    # Check environment variables and secrets
    database_url = get_secret_or_env('database-url', 'DATABASE_URL')
    has_database_url = database_url is not None and database_url != 'sqlite:///default.db'
    
    secret_key = get_secret_or_env('flask-secret-key', 'FLASK_SECRET_KEY') 
    has_secret_key = secret_key is not None and secret_key != 'default_secret_key'
    
    meshy_api_key = get_secret_or_env('meshy-api-key', 'MESHY_API_KEY')
    has_api_key = meshy_api_key is not None
    
    has_storage_bucket = bool(os.getenv('STORAGE_BUCKET'))
    
    return render_template_string(
        html_template,
        db_ok=db_ok,
        db_error=db_error,
        has_database_url=has_database_url,
        has_secret_key=has_secret_key,
        has_storage_bucket=has_storage_bucket,
        has_api_key=has_api_key,
        debug_mode=current_app.debug,
        username=current_user.username
    )

@routes_bp.route('/debug')
def debug():
    """Debug endpoint that shows application state."""
    from main import db
    try:
        # Check database connection
        db_status = "connected"
        try:
            db.session.execute("SELECT 1")
        except Exception as e:
            db_status = f"error: {str(e)}"
            
        # Check imported modules
        modules = list(sys.modules.keys())
        
        return jsonify({
            "status": "ok",
            "database": db_status,
            "loaded_modules": modules,
            "python_path": sys.path,
            "environment": {
                "DATABASE_URL": bool(os.getenv('DATABASE_URL')),
                "FLASK_SECRET_KEY": bool(os.getenv('FLASK_SECRET_KEY')),
                "STORAGE_BUCKET": bool(os.getenv('STORAGE_BUCKET')),
                "PORT": os.getenv('PORT')
            }
        })
    except Exception as e:
        logger.exception("Error in debug endpoint")
        return jsonify({"status": "error", "error": str(e)}), 500

@routes_bp.route('/routes')
def show_routes():
    """Shows all registered routes in the application."""
    routes = []
    
    for rule in current_app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": sorted(list(rule.methods)),
            "path": str(rule)
        })
    
    # Create a simple HTML page to display routes
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Application Routes</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 100%; }
            table, th, td { border: 1px solid #ddd; }
            th, td { padding: 10px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .back-link { margin: 20px 0; }
            .back-link a { padding: 10px; background-color: #4CAF50; color: white; 
                          text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>Registered Application Routes</h1>
        
        <div class="back-link">
            <a href="/">Back to Home</a>
        </div>
        
        <table>
            <tr>
                <th>Endpoint</th>
                <th>Methods</th>
                <th>Path</th>
            </tr>
            {% for route in routes %}
            <tr>
                <td>{{ route.endpoint }}</td>
                <td>{{ route.methods|join(', ') }}</td>
                <td>{{ route.path }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    
    return render_template_string(
        html_template,
        routes=routes
    )
