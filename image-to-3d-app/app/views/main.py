from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.user import User
from app.utils.cloud_storage import upload_image
from app.utils.meshy_api import convert_image
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            image_url = upload_image(file)
            model_url = convert_image(image_url)
            flash('Image uploaded and converted successfully!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('No file selected!', 'danger')
    return render_template('user/upload.html')

@main.route('/account')
def account():
    # Assuming user is logged in and user_id is available
    user_id = 1  # Replace with actual user ID from session
    user = User.query.get(user_id)
    return render_template('user/account.html', user=user)