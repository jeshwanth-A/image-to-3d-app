# Use the official Node.js image
FROM node:18-slim

# Create app directory
WORKDIR /usr/src/app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install --production

# Copy application files
COPY . .

# Expose the port the app will run on
EXPOSE 8080

# Command to run the application
CMD ["node", "server.js"]
