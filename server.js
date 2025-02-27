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

// Initialize application
async function initializeApp() {
  try {
    // Get secrets from Google Secret Manager
    secrets = await initializeSecrets();
    
    // Initialize database connection
    await initializeDatabase(secrets.dbUrl);
    
    console.log('Application initialized successfully');
  } catch (error) {
    console.error('Application initialization failed:', error);
    process.exit(1);
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

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Start the server
app.listen(port, async () => {
  await initializeApp();
  console.log(`Server running on port ${port}`);
});

// Error handling for unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});
