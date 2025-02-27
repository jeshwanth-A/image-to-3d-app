#!/bin/bash
set -e

# Echo commands for debugging
set -x

# Print environment for debugging (hide sensitive values)
echo "ENVIRONMENT:"
env | grep -v -E 'SECRET|KEY|PASSWORD|TOKEN' | sort

# Make sure we're in the right directory
cd /app

# Run admin setup script to ensure admin user exists
echo "Setting up admin user..."
python /app/admin_setup.py
ADMIN_SETUP_STATUS=$?

# Print status
echo "Admin setup exit code: $ADMIN_SETUP_STATUS"

# Make sure secrets.py is found
if [ -f /app/secrets.py ]; then
    echo "secrets.py found"
else
    echo "WARNING: secrets.py not found!"
fi

# Check for model definitions
echo "Checking models..."
if [ -f /app/models.py ]; then
    echo "models.py found"
else
    echo "No models.py file, User model is likely defined in main.py"
fi

# Start the application with gunicorn
echo "Starting application..."
exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 wsgi:application
