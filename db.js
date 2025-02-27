const mysql = require('mysql2/promise');
let pool = null;

/**
 * Initialize the database connection pool
 * 
 * @param {string} dbUrl - Database connection URL
 */
async function initializeDatabase(dbUrl) {
  try {
    pool = mysql.createPool(dbUrl);
    // Test the connection
    const connection = await pool.getConnection();
    connection.release();
    console.log('Database connection established successfully');
    
    // Create users table if it doesn't exist
    await pool.execute(`
      CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    return pool;
  } catch (error) {
    console.error('Database initialization failed:', error);
    throw error;
  }
}

/**
 * Get the database connection pool
 */
function getDb() {
  if (!pool) {
    throw new Error('Database not initialized');
  }
  return pool;
}

module.exports = {
  initializeDatabase,
  getDb
};
