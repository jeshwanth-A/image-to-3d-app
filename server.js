const express = require('express');
const cors = require('cors');
const { initializeSecrets } = require('./secrets');
const { initializeDatabase } = require('./db');
const { registerUser, loginUser, authenticateToken } = require('./auth');

const app = express();
const port = process.env.PORT || 8080;

// Middleware
app.use(cors());
app.use(express.json());

let secrets = null;
let server = null;

// Initialize application
async function initializeApp() {
  try {
    console.log('Starting initialization process...');
    
    // Get secrets from Google Secret Manager
    console.log('Fetching secrets from Google Secret Manager...');
    secrets = await initializeSecrets();
    console.log('Secrets retrieved successfully');
    
    // Initialize database connection
    console.log('Initializing database connection...');
    await initializeDatabase(secrets.dbUrl);
    
    console.log('Application initialized successfully');
  } catch (error) {
    console.error('Application initialization failed:', error);
    // Don't exit immediately - let Cloud Run retry or handle as needed
    throw error;
  }
}

// Authentication routes
app.post('/api/register', async (req, res) => {
  try {
    const { email, password, name } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    
    const user = await registerUser(email, password, name);
    res.status(201).json({ message: 'User registered successfully', user });
  } catch (error) {
    if (error.message === 'User already exists') {
      return res.status(409).json({ error: 'User already exists' });
    }
    res.status(500).json({ error: 'Registration failed' });
  }
});

app.post('/api/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    
    const result = await loginUser(email, password, secrets.flaskSecretKey);
    res.json(result);
  } catch (error) {
    if (error.message === 'Invalid credentials') {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    res.status(500).json({ error: 'Login failed' });
  }
});

// Protected route example
app.get('/api/protected', authenticateToken(secrets.flaskSecretKey), (req, res) => {
  res.json({ 
    message: 'This is a protected route',
    user: req.user,
    meshyApiKey: secrets.meshyApiKey // Example of using the Meshy API key
  });
});

// Health check endpoint - important for Cloud Run
app.get('/', (req, res) => {
  res.status(200).send('Server is up and running');
});

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Graceful shutdown handler
function shutdownGracefully() {
  console.log('Shutting down gracefully...');
  if (server) {
    server.close(() => {
      console.log('HTTP server closed');
      process.exit(0);
    });
    
    // Force close after 10s if server doesn't exit cleanly
    setTimeout(() => {
      console.error('Forcing server shutdown');
      process.exit(1);
    }, 10000);
  } else {
    process.exit(0);
  }
}

// Start the server
async function startServer() {
  try {
    // We initialize first before starting HTTP server
    await initializeApp();
    
    // Create the HTTP server
    server = app.listen(port, () => {
      console.log(`Server running on port ${port}`);
    });
    
    // Handle common termination signals
    process.on('SIGTERM', shutdownGracefully);
    process.on('SIGINT', shutdownGracefully);
    
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Error handling for unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  // Don't crash the app, just log it
});

// Start everything up
startServer();
