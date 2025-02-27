#!/bin/bash
set -e

# Run admin setup script to ensure admin user exists
echo "Setting up admin user..."
python /app/admin_setup.py

# Start the application with gunicorn
echo "Starting application..."
exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 wsgi:application
