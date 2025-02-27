import os
import base64
import requests
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from google.cloud import storage
from werkzeug.utils import secure_filename
from models import Task, db

upload_bp = Blueprint('upload', __name__)

# Google Cloud Storage setup (no service account file needed in Cloud Run)
storage_client = storage.Client()
bucket = storage_client.bucket(os.getenv('GCS_BUCKET_NAME'))

# Meshy API setup
MESHY_API_URL = 'https://api.meshy.ai/v1/image-to-3d'  # Hypothetical
MESHY_API_KEY = os.getenv('MESHY_API_KEY')

@upload_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@upload_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400
    
    filename = secure_filename(file.filename)
    user_folder = f'{current_user.id}'
    blob = bucket.blob(f'{user_folder}/{filename}')
    blob.upload_from_file(file)

    # Convert file to base64 for Meshy API
    file.seek(0)
    file_content = file.read()
    base64_image = base64.b64encode(file_content).decode('utf-8')
    data_uri = f'data:image/{file.content_type.split("/")[1]};base64,{base64_image}'

    # Create task with Meshy API
    headers = {'Authorization': f'Bearer {MESHY_API_KEY}'}
    data = {'image_url': data_uri}
    response = requests.post(MESHY_API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        task_id = response.json().get('task_id')  # Adjust based on Meshy API
        new_task = Task(user_id=current_user.id, task_id=task_id, image_file=filename)
        db.session.add(new_task)
        db.session.commit()
        return jsonify({'message': 'File uploaded and task created'})
    return jsonify({'error': 'Failed to create task'}), 500

@upload_bp.route('/tasks')
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    task_list = [{'id': t.id, 'status': t.status, 'image_file': t.image_file, 'model_file': t.model_file} for t in tasks]
    return jsonify(task_list)

def check_task_status():
    pending_tasks = Task.query.filter_by(status='pending').all()
    headers = {'Authorization': f'Bearer {MESHY_API_KEY}'}
    for task in pending_tasks:
        status_url = f'{MESHY_API_URL}/{task.task_id}'  # Adjust based on Meshy API
        response = requests.get(status_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'SUCCEEDED':
                model_url = data['model_urls']['glb']  # Adjust based on API
                model_response = requests.get(model_url)
                if model_response.status_code == 200:
                    model_filename = f'{task.id}_model.glb'
                    model_blob = bucket.blob(f'{task.user_id}/{model_filename}')
                    model_blob.upload_from_string(model_response.content)
                    task.model_file = model_filename
                    task.status = 'completed'
                    db.session.commit()
            elif data.get('status') == 'FAILED':
                task.status = 'failed'
                db.session.commit()