"""
Admin routes for the Image-to-3D app.
"""
import os
import json
import logging
import traceback
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User
from gcp_secrets import get_secret_or_env
from google.cloud import storage

# Configure logging
logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard page."""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin panel')
        return redirect(url_for('auth.profile'))
    
    # Get all users from the database
    users = User.query.all()
    
    # Check service connectivity
    service_status = check_services()
    
    return render_template('admin.html', users=users, status=service_status)

def check_services():
    """Check the status of required services."""
    status = {
        'database': {'status': 'unknown', 'message': 'Not checked'},
        'bucket': {'status': 'unknown', 'message': 'Not checked'},
        'meshy_api': {'status': 'unknown', 'message': 'Not checked'}
    }
    
    # Check database connection
    try:
        result = db.session.execute('SELECT 1').scalar()
        if result == 1:
            status['database'] = {
                'status': 'ok',
                'message': 'Connected successfully'
            }
    except Exception as e:
        status['database'] = {
            'status': 'error',
            'message': str(e)
        }
        logger.error(f"Database check error: {e}")
    
    # Check bucket access
    try:
        bucket_name = os.environ.get('GCS_BUCKET_NAME', 'project-2-450420-images')
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        if bucket.exists():
            status['bucket'] = {
                'status': 'ok',
                'message': f'Bucket {bucket_name} accessible'
            }
        else:
            status['bucket'] = {
                'status': 'error',
                'message': f'Bucket {bucket_name} does not exist'
            }
    except Exception as e:
        status['bucket'] = {
            'status': 'error',
            'message': str(e)
        }
        logger.error(f"Bucket check error: {e}")
    
    # Check Meshy API key
    try:
        meshy_api_key = get_secret_or_env('meshy-api-key', 'MESHY_API_KEY')
        if meshy_api_key:
            status['meshy_api'] = {
                'status': 'ok',
                'message': 'API key found'
            }
        else:
            status['meshy_api'] = {
                'status': 'error',
                'message': 'API key not found'
            }
    except Exception as e:
        status['meshy_api'] = {
            'status': 'error',
            'message': str(e)
        }
        logger.error(f"Meshy API check error: {e}")
    
    return status
