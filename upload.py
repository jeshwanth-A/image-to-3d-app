import os
import base64
import requests
from flask import Blueprint, render_template, request, jsonify, render_template_string, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from google.cloud import storage
from werkzeug.utils import secure_filename
from main import db
import logging
import uuid
import json
import traceback
from datetime import datetime
from gcp_secrets import get_secret_or_env
import meshy_api

# Configure logging
logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

# Google Cloud Storage setup (no service account file needed in Cloud Run)
storage_client = storage.Client()
bucket = storage_client.bucket(os.getenv('GCS_BUCKET_NAME', 'project-2-450420-images'))

# Meshy API setup
MESHY_API_URL = 'https://api.meshy.ai/v1/image-to-3d'  # Hypothetical
MESHY_API_KEY = os.getenv('MESHY_API_KEY')

# Define a simple model for uploads
class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    original_filename = db.Column(db.String(100), nullable=False)
    task_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')
    result_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Upload {self.filename}>'

# HTML template for the upload form
UPLOAD_FORM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Upload Image for 3D Conversion</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1, h2 { color: #333; }
        form { background-color: #f9f9f9; padding: 20px; border-radius: 5px; max-width: 500px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="file"] { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; border-radius: 4px; }
        .error { color: #cc0000; margin-bottom: 15px; }
        .success { color: #4CAF50; margin-bottom: 15px; }
        .back-link { margin: 20px 0; }
        .back-link a { padding: 10px; background-color: #4CAF50; color: white; 
                      text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Upload Image for 3D Conversion</h1>
    
    <div class="back-link">
        <a href="/">Back to Home</a>
    </div>
    
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    
    {% if success %}
    <div class="success">{{ success }}</div>
    {% endif %}
    
    <form method="POST" action="{{ url_for('upload.upload_form') }}" enctype="multipart/form-data">
        <div class="form-group">
            <label for="image">Select Image (JPG, PNG)</label>
            <input type="file" id="image" name="image" accept=".jpg,.jpeg,.png" required>
        </div>
        <button type="submit">Upload & Convert to 3D</button>
    </form>
    
    <h2>Your Previous Uploads</h2>
    <table border="1" style="width: 100%; border-collapse: collapse;">
        <tr>
            <th>Original Filename</th>
            <th>Upload Date</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
        {% for upload in uploads %}
        <tr>
            <td>{{ upload.original_filename }}</td>
            <td>{{ upload.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
            <td>{{ upload.status }}</td>
            <td>
                {% if upload.status == 'completed' %}
                <a href="{{ upload.result_url }}" target="_blank">View 3D Model</a>
                {% else %}
                <a href="{{ url_for('upload.check_status', upload_id=upload.id) }}">Check Status</a>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@upload_bp.route('/', methods=['GET', 'POST'])
@login_required
def upload_form():
    error = None
    success = None
    
    try:
        # Get user's previous uploads
        uploads = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.created_at.desc()).all()
        
        if request.method == 'POST':
            try:
                # Check if the post request has the file part
                if 'image' not in request.files:
                    error = "No file part"
                else:
                    file = request.files['image']
                    
                    # If user does not select file, browser also
                    # submits an empty part without filename
                    if file.filename == '':
                        error = "No selected file"
                    else:
                        if file and allowed_file(file.filename):
                            # Generate a secure filename
                            original_filename = secure_filename(file.filename)
                            filename = f"{uuid.uuid4()}_{original_filename}"
                            
                            # Create temp directory if it doesn't exist
                            os.makedirs('/tmp', exist_ok=True)
                            
                            # Save file locally
                            file_path = os.path.join('/tmp', filename)
                            file.save(file_path)
                            
                            # Create upload record in database
                            new_upload = Upload(
                                user_id=current_user.id,
                                filename=filename,
                                original_filename=original_filename,
                                status='pending'
                            )
                            db.session.add(new_upload)
                            db.session.commit()
                            logger.info(f"Created upload record for {filename}")
                            
                            # Upload to Meshy API
                            try:
                                # Initialize Meshy API first
                                if not meshy_api.init_api():
                                    raise Exception("Meshy API initialization failed - API key not found")
                                
                                # Set optional processing settings 
                                settings = {
                                    "enable_pbr": False,
                                    "should_remesh": True,
                                    "should_texture": True
                                }
                                
                                # Upload to Meshy API
                                task_id, api_error = meshy_api.upload_image_to_3d(file_path, settings)
                                
                                if api_error:
                                    error = f"Meshy API error: {api_error}"
                                    new_upload.status = 'failed'
                                    db.session.commit()
                                elif task_id:
                                    # Update record with task ID
                                    new_upload.task_id = task_id
                                    new_upload.status = 'processing'
                                    db.session.commit()
                                    success = "File uploaded successfully! 3D conversion in progress."
                                else:
                                    error = "Failed to submit the image to the 3D conversion service."
                            except Exception as e:
                                logger.error(f"Error calling Meshy API: {e}")
                                logger.error(traceback.format_exc())
                                error = f"API Error: {str(e)}"
                                new_upload.status = 'failed'
                                db.session.commit()
                        else:
                            error = "File type not allowed. Please upload a JPG or PNG image."
            except Exception as e:
                db.session.rollback()
                logger.error(f"Upload error: {e}")
                logger.error(traceback.format_exc())
                error = f"An error occurred during upload: {str(e)}"
        
        # Render template with results
        return render_template_string(
            UPLOAD_FORM_TEMPLATE, 
            error=error, 
            success=success, 
            uploads=uploads
        )
    
    except Exception as e:
        logger.error(f"Fatal error in upload_form: {e}")
        logger.error(traceback.format_exc())
        
        # Return a basic error page if somethin2g went very wrong
        error_template = """
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Application Error</h1>
            <p>Sorry, an error occurred while processing your request.</p>
            <p>Error details: {{ error }}</p>
            <p><a href="/">Return to homepage</a></p>
        </body>
        </html>
        """
        return render_template_string(error_template, error=str(e)), 500

@upload_bp.route('/check-status/<int:upload_id>')
@login_required
def check_status(upload_id):
    try:
        upload = Upload.query.get(upload_id)
        
        if not upload:
            return jsonify({"error": "Upload not found"}), 404
            
        if upload.user_id != current_user.id:
            return jsonify({"error": "Unauthorized access"}), 403
            
        # If already completed, just return the result
        if upload.status == 'completed':
            return jsonify({
                "status": "completed",
                "result_url": upload.result_url
            })
            
        # Otherwise check with the API for updates
        if upload.task_id:
            # Simulated API check
            status, result_url = check_meshy_task_status(upload.task_id)
            
            if status != upload.status:
                upload.status = status
                if result_url:
                    upload.result_url = result_url
                db.session.commit()
                
            return jsonify({
                "status": status,
                "result_url": result_url
            })
        else:
            return jsonify({"status": "error", "error": "No task ID found"}), 400
            
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# Helper function to check if file is allowed
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Replace the simulated API functions with real ones:

def upload_to_meshy_api(file_path):
    """Upload image to Meshy API for 3D conversion."""
    logger.info(f"Uploading {file_path} to Meshy API")
    
    # Set optional processing settings
    settings = {
        "promptText": "High quality detailed 3D model",
        "negativePromptText": "low quality, bad geometry",
        "taskType": "image-to-3d"
    }
    
    # Call the Meshy API
    task_id, error = meshy_api.upload_image_to_3d(file_path, settings)
    
    if error:
        logger.error(f"Meshy API upload error: {error}")
        raise Exception(f"Meshy API error: {error}")
        
    logger.info(f"Successfully submitted to Meshy API. Task ID: {task_id}")
    return task_id

def check_meshy_task_status(task_id):
    """Check task status with Meshy API."""
    logger.info(f"Checking status of task {task_id}")
    
    # Call the Meshy API to check status
    status, result_url, error = meshy_api.check_task_status(task_id)
    
    if error and status == "failed":
        logger.error(f"Meshy API task failed: {error}")
        return "failed", None
    
    logger.info(f"Task {task_id} status: {status}")
    
    # For completed tasks, store the result URL
    if status == "completed" and result_url:
        logger.info(f"Task {task_id} completed. Result URL: {result_url}")
        return "completed", result_url
    
    # Still processing
    return status, None

def check_task_status():
    """Check status of all processing uploads."""
    try:
        # Get all uploads with 'processing' status
        processing_uploads = Upload.query.filter_by(status='processing').all()
        logger.info(f"Checking status of {len(processing_uploads)} processing tasks")
        
        for upload in processing_uploads:
            if upload.task_id:
                # Check status with real API
                status, result_url = check_meshy_task_status(upload.task_id)
                
                if status != upload.status:
                    upload.status = status
                    if result_url:
                        upload.result_url = result_url
                    db.session.commit()
                    logger.info(f"Updated task {upload.task_id} to status: {status}")
    
    except Exception as e:
        logger.error(f"Error in check_task_status: {e}")
        logger.error(traceback.format_exc())
        db.session.rollback()