from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from functools import wraps
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///test.db")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)  # In production, store hashed passwords

Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
db_session = DBSession()

# Decorator for login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator for admin required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin') != True:
            flash("Admin access required.")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Sign up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Hash this in production!
        # Simple check: avoid duplicate usernames
        if db_session.query(User).filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('signup'))
        new_user = User(username=username, password=password)
        db_session.add(new_user)
        db_session.commit()
        flash("Account created, please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

# Sign in route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db_session.query(User).filter_by(username=username, password=password).first()
        if user:
            session['user'] = username
            flash("Logged in successfully!")
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.")
    return render_template('login.html')

# User dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['user'])

# Admin login for the admin dashboard
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_user = request.form['username']
        admin_pass = request.form['password']
        # Admin credentials are hard-coded as per your requirement
        if admin_user == "mvsr" and admin_pass == "mvsr":
            session['admin'] = True
            flash("Welcome Admin!")
            return redirect(url_for('admin'))
        flash("Invalid admin credentials.")
    return render_template('admin_login.html')

# Admin dashboard: List all accounts and tickboxes for data fetched
@app.route('/admin')
@admin_required
def admin():
    users = db_session.query(User).all()
    # Dummy flags for demonstration; implement actual checks for SQL and bucket fetches
    sql_fetched = True  # Replace with actual logic
    bucket_fetched = False  # Replace with actual logic
    return render_template('admin.html', users=users, sql_fetched=sql_fetched, bucket_fetched=bucket_fetched)

if __name__ == '__main__':
    app.run(debug=True)