# Image to 3D App

This project is a web application that allows users to sign up, log in, and upload images which are then processed into 3D models using the Meshy API. The application is built with Flask and utilizes a PostgreSQL database for user management and image storage.

## Features

- User authentication (sign up, login)
- Admin dashboard for user management
- Image upload functionality
- Integration with Meshy API for image conversion
- Google Cloud Storage for storing images

## Project Structure

```
image-to-3d-app
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── static
│   │   ├── css
│   │   │   └── main.css
│   │   └── js
│   │       └── main.js
│   ├── templates
│   │   ├── admin
│   │   │   ├── dashboard.html
│   │   │   └── users.html
│   │   ├── auth
│   │   │   ├── login.html
│   │   │   └── signup.html
│   │   ├── base.html
│   │   ├── index.html
│   │   └── user
│   │       ├── account.html
│   │       └── upload.html
│   ├── utils
│   │   ├── __init__.py
│   │   ├── cloud_storage.py
│   │   └── meshy_api.py
│   └── views
│       ├── __init__.py
│       ├── admin.py
│       ├── auth.py
│       └── main.py
├── migrations
│   └── README.md
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
└── run.py
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd image-to-3d-app
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file based on the `.env.example` file and fill in the required values.

5. **Run the application:**
   ```
   python run.py
   ```

## Database Migrations

For managing database migrations, refer to the `migrations/README.md` file.

## License

This project is licensed under the MIT License. See the LICENSE file for details.