"""
Install all required dependencies for the application
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip."""
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    """Install all required dependencies."""
    print("Checking and installing dependencies...")
    
    # Core dependencies
    dependencies = [
        "flask==2.0.1",
        "flask-login==0.5.0",
        "flask-sqlalchemy==2.5.1",
        "sqlalchemy==1.4.23",
        "google-cloud-storage==1.42.0",
        "google-cloud-secret-manager==2.12.0",
        "requests==2.26.0",
        "python-dotenv==0.19.0",
        "werkzeug==2.0.1",
        "psycopg2-binary==2.9.3"
    ]
    
    # Install each dependency
    for dep in dependencies:
        install_package(dep)
    
    print("\nAll dependencies installed successfully!")
    print("You can now run the application or test scripts.")

if __name__ == "__main__":
    main()
