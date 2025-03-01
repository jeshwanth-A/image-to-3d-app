# Use official Node.js image
FROM node:18

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies and build React
RUN npm install && npm run build

# Install a lightweight web server
RUN npm install -g serve

# Expose the correct port for Cloud Run
EXPOSE 8080

# Serve the built React app on port 8080
CMD ["serve", "-s", "build", "-l", "8080"]