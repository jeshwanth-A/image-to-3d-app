# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose the port that Flask (or Gunicorn) will run on
EXPOSE 8080

# Use Gunicorn as the production server
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]