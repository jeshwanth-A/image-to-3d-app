import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:<ldrago55g>@/image_to_3d_db?host=/cloudsql/project-2-450420:us-central1:arportal')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'ad72ade7f0bce650632fb2db88eba29f19ddd9c20be2d098')
    MESHY_API_KEY = os.getenv('MESHY_API_KEY', 'msy_gXlokg8zy7u2PhYDva8gSGb4S9PTNJaiPMx7')
    GOOGLE_CLOUD_BUCKET = os.getenv('GOOGLE_CLOUD_BUCKET', 'your-bucket-name')