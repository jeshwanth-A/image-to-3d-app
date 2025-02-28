# Build React Frontend
FROM node:18 AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Set up Python Environment for FastAPI
FROM python:3.9 AS backend
WORKDIR /app
COPY backend/ /app/
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] &

# Set up Nginx
FROM nginx:latest
COPY --from=frontend /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]