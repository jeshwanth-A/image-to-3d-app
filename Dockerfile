# Build React Frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Final image
FROM python:3.9-slim
WORKDIR /app

# Install nginx
RUN apt-get update && apt-get install -y nginx && apt-get clean

# Setup backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/

# Copy frontend build from the previous stage
COPY --from=frontend-build /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port - Cloud Run will override this with PORT env variable
EXPOSE 8080

# Start both services
CMD ["/app/start.sh"]