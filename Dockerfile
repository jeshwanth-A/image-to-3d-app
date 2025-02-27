# Use an official Python runtime as base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the required port
EXPOSE 8080

# Start the app using Gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 main:app