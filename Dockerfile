FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Expose the port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=main.py

# Run the application using Gunicorn
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:5000", "wsgi:app"]
