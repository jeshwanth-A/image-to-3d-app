const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { getDb } = require('./db');

/**
 * Register a new user
 */
async function registerUser(email, password, name) {
  const db = getDb();
  
  try {
    // Check if user already exists
    const [existingUsers] = await db.execute(
      'SELECT * FROM users WHERE email = ?',
      [email]
    );
    
    if (existingUsers.length > 0) {
      throw new Error('User already exists');
    }
    
    // Hash the password
    const hashedPassword = await bcrypt.hash(password, 10);
    
    // Insert the new user
    const [result] = await db.execute(
      'INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
      [email, hashedPassword, name]
    );
    
    return { id: result.insertId, email, name };
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
}

/**
 * Login a user
 */
async function loginUser(email, password, secretKey) {
  const db = getDb();
  
  try {
    // Find the user
    const [users] = await db.execute(
      'SELECT * FROM users WHERE email = ?',
      [email]
    );
    
    if (users.length === 0) {
      throw new Error('Invalid credentials');
    }
    
    const user = users[0];
    
    // Compare passwords
    const isPasswordValid = await bcrypt.compare(password, user.password);
    
    if (!isPasswordValid) {
      throw new Error('Invalid credentials');
    }
    
    // Generate JWT token
    const token = jwt.sign(
      { id: user.id, email: user.email },
      secretKey,
      { expiresIn: '24h' }
    );
    
    return {
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name
      }
    };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

/**
 * Middleware to verify JWT token
 */
function authenticateToken(secretKey) {
  return (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({ error: 'Authentication token required' });
    }
    
    jwt.verify(token, secretKey, (err, user) => {
      if (err) {
        return res.status(403).json({ error: 'Invalid or expired token' });
      }
      
      req.user = user;
      next();
    });
  };
}

module.exports = {
  registerUser,
  loginUser,
  authenticateToken
};
