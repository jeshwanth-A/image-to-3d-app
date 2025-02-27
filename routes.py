from flask import Blueprint, jsonify, current_app
import sys
import os
import datetime
import logging

routes_bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

@routes_bp.route('/')
def index():
    return "Hello World! The application is running."

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
