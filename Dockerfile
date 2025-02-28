FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py
ENV USERS_FILE=/data/users.json

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create data directory for persisting users.json
RUN mkdir -p /data && chmod 777 /data

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Create a non-root user and set permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod 755 /app

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 5000

# Run the application using Gunicorn with config
CMD ["gunicorn", "--config", "gunicorn_config.py", "wsgi:app"]
