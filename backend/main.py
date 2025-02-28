import os
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from google.cloud import secretmanager
from passlib.context import CryptContext
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Allow CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Cloud Secret Manager Client
client = secretmanager.SecretManagerServiceClient()

# Fetch secrets from Google Cloud Secret Manager
def get_secret(secret_name):
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=secret_path)
    return response.payload.data.decode("UTF-8")

# Retrieve database URL & secret key
DATABASE_URL = get_secret("database-url")
SECRET_KEY = get_secret("flask-secret-key")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    email: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_jwt(email: str):
    expiration = datetime.utcnow() + timedelta(hours=12)
    payload = {"sub": email, "exp": expiration}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

@app.post("/api/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = pwd_context.hash(user.password)
    new_user = User(email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "User signed up!", "token": create_jwt(user.email)}

@app.post("/api/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if not existing_user or not pwd_context.verify(user.password, existing_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful!", "token": create_jwt(user.email)}