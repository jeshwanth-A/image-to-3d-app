# Portal - Image to 3D Model Generator

🚀 **Transform your 2D images into stunning 3D models with AI-powered technology!**

Portal is a Flask-based web application that converts 2D images into 3D models using the Tripo API. It features user authentication, cloud storage integration, and an immersive Unity WebGL game experience.

## ✨ Features

### Core Functionality
- **AI-Powered 3D Generation**: Convert any 2D image into a 3D model using Tripo API
- **User Authentication**: Secure signup/login system with admin panel
- **Cloud Storage**: Google Cloud Storage integration for scalable file management
- **Real-time Progress**: Monitor 3D model generation progress with live updates
- **Model Management**: View, rename, and delete your generated 3D models

### Gaming Experience
- **Unity WebGL Integration**: Immersive 3D portal game built with Unity
- **Cross-Platform**: Works on desktop and mobile browsers
- **Interactive UI**: Intuitive interface for seamless user experience

### Admin Features
- **User Management**: Admin panel to manage users and their models
- **System Monitoring**: Track usage and manage system resources
- **Model Analytics**: View all generated models across the platform

## 🛠️ Technology Stack

- **Backend**: Flask (Python 3.9+)
- **Database**: SQLite with SQLAlchemy ORM
- **Cloud Storage**: Google Cloud Storage
- **3D API**: Tripo API for image-to-3D conversion
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Game Engine**: Unity WebGL
- **Deployment**: Docker + Google Cloud Run
- **Authentication**: Flask-Login with secure password hashing

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud Platform account
- Tripo API key ([Get one here](https://tripo3d.ai/))
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jeshwanth-A/image-to-3d-app.git
   cd image-to-3d-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   export FLASK_SECRET_KEY="your-secret-key-here"
   export TRIPO_API_KEY="your-tripo-api-key"
   export BUCKET_NAME="your-gcs-bucket-name"
   export DATABASE_URL="sqlite:///app.db"  # Optional: defaults to SQLite
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and navigate to `http://localhost:8080`
   - Default admin credentials: `admin` / `admin123`

## 🎮 How to Use

### Sample Model
The repository includes a sample bike model (`bike.jpeg` and `bike_model.glb`) to demonstrate the image-to-3D conversion process.

### For Users

1. **Sign Up**: Create a new account or login with existing credentials
2. **Upload Image**: Select and upload a 2D image (JPEG/PNG)
3. **Generate Model**: The system will process your image using AI
4. **Monitor Progress**: Watch real-time progress updates
5. **Download & Play**: Access your 3D model and explore it in the Unity game

### For Developers

#### API Endpoints

The application provides RESTful API endpoints for integration:

```http
POST /api/signup
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

```http
POST /api/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

```http
GET /api/models
Authorization: Bearer <token>
```

#### Model Status Checking

```http
GET /status/<model_id>
Authorization: Bearer <token>
```

Response:
```json
{
  "status": "SUCCEEDED|IN_PROGRESS|FAILED",
  "model_url": "https://storage.googleapis.com/...",
  "progress": 85
}
```

## 🐳 Docker Deployment

### Build and Run Locally

```bash
# Build the Docker image
docker build -t portal-app .

# Run the container
docker run -p 8080:8080 \
  -e FLASK_SECRET_KEY="your-secret-key" \
  -e TRIPO_API_KEY="your-tripo-api-key" \
  -e BUCKET_NAME="your-bucket-name" \
  portal-app
```

### Google Cloud Run Deployment

1. **Setup Google Cloud Project**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Configure Cloud Build**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy portal-app \
     --image gcr.io/YOUR_PROJECT_ID/portal-app \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## 📁 Project Structure

```
image-to-3d-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── cloudbuild.yaml       # Google Cloud Build config
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── login.html        # Login page
│   ├── signup.html       # Registration page
│   ├── upload.html       # Image upload page
│   ├── models.html       # Model management
│   └── admin_panel.html  # Admin interface
├── static/              # Static assets
│   ├── index.html       # Unity WebGL game
│   ├── Build/           # Unity build files
│   └── TemplateData/    # Unity template assets
└── README.md           # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FLASK_SECRET_KEY` | Flask session secret key | Yes |
| `TRIPO_API_KEY` | Tripo API key for 3D generation | Yes |
| `BUCKET_NAME` | Google Cloud Storage bucket name | Yes |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |

### Database Models

```python
# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Model storage
class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(256), nullable=False)
    model_url = db.Column(db.String(256), nullable=True)
    task_id = db.Column(db.String(64), nullable=True)
    name = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
```

## 🔐 Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **Session Management**: Flask-Login for secure session handling
- **CORS Protection**: Configured for API security
- **Input Validation**: WTForms for form validation and CSRF protection
- **Admin Controls**: Separate admin interface with elevated permissions

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
export FLASK_ENV=development
python app.py
```

## 📸 Screenshots

*Screenshots will be added soon to showcase the application interface*

### Features Preview
- **Homepage**: Clean, modern interface with easy navigation
- **Upload Process**: Drag-and-drop image upload with progress tracking
- **Model Viewer**: Interactive 3D model display and management
- **Unity Game**: Immersive WebGL portal experience
- **Admin Panel**: Comprehensive user and model management dashboard

## 🔍 Troubleshooting

### Common Issues

1. **Tripo API Error 403**
   - Check your API key validity
   - Ensure your account has sufficient credits
   - Verify API key permissions

2. **Google Cloud Storage Issues**
   - Confirm bucket exists and is accessible
   - Check service account permissions
   - Verify bucket name in environment variables

3. **Database Connection Errors**
   - Ensure SQLite file is writable
   - Check database URL format
   - Verify database directory exists

### Debug Mode

Enable debug mode for development:
```python
app.debug = True
```

View logs:
```bash
# Docker logs
docker logs <container-id>

# Cloud Run logs
gcloud logs read --service=portal-app --limit=100
```

## 📊 Performance

- **Image Processing**: ~30-60 seconds per model
- **Storage**: Efficient cloud storage with CDN
- **Scalability**: Auto-scaling with Cloud Run
- **Supported Formats**: JPEG, PNG images up to 10MB

## 🔄 API Rate Limits

- **Tripo API**: Check your plan limits
- **Google Cloud Storage**: 5000 requests/second
- **Application**: No built-in rate limiting (implement as needed)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Tripo AI** for the amazing 3D generation API
- **Google Cloud Platform** for reliable hosting and storage
- **Unity Technologies** for the WebGL platform
- **Flask Community** for the excellent web framework

## 📞 Support

For support, please:
1. Check the [Issues](https://github.com/jeshwanth-A/image-to-3d-app/issues) page
2. Create a new issue with detailed description
3. Contact the maintainers

---

**Made with ❤️ by the Portal Team**

*Transform your imagination into reality with Portal - where 2D becomes 3D!*