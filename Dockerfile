# Use official Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

# Expose the correct port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=False

# Run with gunicorn for better production deployment
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --log-level info wsgi:application