# Use official Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt  # 👈 Ensure all dependencies are installed

# Expose the correct port
EXPOSE 8080

# Set PORT environment variable
ENV PORT=8080

# Run FastAPI with Uvicorn on port 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]