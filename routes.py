from flask import Blueprint, jsonify, current_app, render_template_string, url_for
import sys
import os
import datetime
import logging

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
        </style>
    </head>
    <body>
        <h1>Image to 3D App</h1>
        <p>The application is running successfully!</p>
        
        <div class="status">
            <strong>Status:</strong> Online
            <br>
            <strong>Time:</strong> {{ current_time }}
        </div>
        
        <h2>Navigation</h2>
        <div class="nav-links">
            {% if auth_url %}<a href="{{ auth_url }}">Login/Register</a>{% endif %}
            {% if upload_url %}<a href="{{ upload_url }}">Upload Images</a>{% endif %}
            <a href="/health">Application Health</a>
            <a href="/routes">View All Routes</a>
        </div>
        
        <div>
            <h3>Debug Links</h3>
            <ul>
                <li><a href="/debug">Debug Information</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    # Try to generate URLs for auth and upload
    auth_url = None
    upload_url = None
    try:
        auth_url = url_for('auth.login')
    except Exception as e:
        logger.error(f"Could not generate auth URL: {e}")
    
    try:
        upload_url = url_for('upload.upload_form')
    except Exception as e:
        logger.error(f"Could not generate upload URL: {e}")
        # Try alternative names
        try:
            upload_url = url_for('upload.index')
        except Exception:
            pass
    
    return render_template_string(
        html_template, 
        current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        auth_url=auth_url,
        upload_url=upload_url
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
            "python_path": sys.path
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
