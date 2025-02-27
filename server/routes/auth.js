const express = require('express');
const router = express.Router();
const { check, validationResult } = require('express-validator');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const auth = require('../middleware/auth');
const config = require('../config');

// @route   GET /auth/login
// @desc    Get login page or authenticate user
// @access  Public
router.get('/login', async (req, res) => {
  try {
    // Check if it's a page request or an authentication request
    if (!req.headers.authorization) {
      // Return login page
      return res.render('login');
    }
    
    // Handle authentication
    const token = req.headers.authorization.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({ error: 'No token, authorization denied' });
    }

    try {
      const decoded = jwt.verify(token, config.jwtSecret);
      req.user = decoded.user;
      return res.json({ user: req.user });
    } catch (err) {
      return res.status(401).json({ error: 'Token is not valid' });
    }
  } catch (err) {
    console.error('Auth error:', err.message);
    res.status(500).json({ error: 'Server error', details: err.message });
  }
});

// @route   POST /auth/login
// @desc    Authenticate user & get token
// @access  Public
router.post('/login', [
  check('email', 'Please include a valid email').isEmail(),
  check('password', 'Password is required').exists()
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const { email, password } = req.body;

  try {
    let user = await User.findOne({ email });

    if (!user) {
      return res.status(400).json({ error: 'Invalid Credentials' });
    }

    const isMatch = await bcrypt.compare(password, user.password);

    if (!isMatch) {
      return res.status(400).json({ error: 'Invalid Credentials' });
    }

    const payload = {
      user: {
        id: user.id
      }
    };

    jwt.sign(
      payload,
      config.jwtSecret,
      { expiresIn: '24h' },
      (err, token) => {
        if (err) throw err;
        res.json({ token });
      }
    );
  } catch (err) {
    console.error('Login error:', err.message);
    res.status(500).json({ error: 'Server error', details: err.message });
  }
});

module.exports = router;
