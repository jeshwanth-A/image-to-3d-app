import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # e.g., postgresql+psycopg2://user:pass@host/dbname
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #c

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Register blueprints
from auth import auth_bp
from upload import upload_bp
app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)

# Background job to check Meshy task statuses
def check_tasks():
    with app.app_context():  # Ensure app context for DB operations
        from upload import check_task_status
        check_task_status()

scheduler = BackgroundScheduler()
scheduler.add_job(check_tasks, 'interval', minutes=5)
scheduler.start()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don’t exist
    port = int(os.getenv('PORT', 8080))  # Default to 8080 for Cloud Run
    app.run(host='0.0.0.0', port=port)