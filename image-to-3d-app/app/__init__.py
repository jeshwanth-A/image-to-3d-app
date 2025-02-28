from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['MESHY_API_KEY'] = os.getenv('MESHY_API_KEY')

db = SQLAlchemy(app)

from app.views import main, auth, admin

app.register_blueprint(main.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)