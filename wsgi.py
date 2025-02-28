from main import app

# Ensure the app variable is properly exported for Gunicorn
if __name__ == "__main__":
    app.run()
