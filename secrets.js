const {SecretManagerServiceClient} = require('@google-cloud/secret-manager');

// Create the Secret Manager client
const client = new SecretManagerServiceClient();

/**
 * Retrieves a secret from Google Secret Manager
 * 
 * @param {string} secretName - Name of the secret to retrieve
 * @returns {Promise<string>} - The secret value
 */
async function getSecret(secretName) {
  try {
    console.log(`Fetching secret: ${secretName}`);
    const projectId = process.env.GOOGLE_CLOUD_PROJECT || process.env.PROJECT_ID;
    
    if (!projectId) {
      throw new Error('GOOGLE_CLOUD_PROJECT or PROJECT_ID environment variable is not set');
    }
    
    console.log(`Using project ID: ${projectId}`);
    const name = `projects/${projectId}/secrets/${secretName}/versions/latest`;
    
    const [version] = await client.accessSecretVersion({
      name: name,
    });

    return version.payload.data.toString();
  } catch (error) {
    console.error(`Error retrieving secret ${secretName}:`, error);
    throw error;
  }
}

/**
 * Initialize all secrets needed for the application
 */
async function initializeSecrets() {
  try {
    // For debugging in Cloud Run
    console.log('Environment variables available:', Object.keys(process.env).join(', '));
    
    // Use environment variables as fallbacks for local development or testing
    const secrets = {
      dbUrl: process.env.DATABASE_URL || await getSecret('database-url'),
      flaskSecretKey: process.env.FLASK_SECRET_KEY || await getSecret('flask-secret-key'),
      meshyApiKey: process.env.MESHY_API_KEY || await getSecret('meshy-api-key')
    };
    
    return secrets;
  } catch (error) {
    console.error('Failed to initialize secrets:', error);
    throw error;
  }
}

module.exports = {
  getSecret,
  initializeSecrets
};
