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
    const projectId = process.env.GOOGLE_CLOUD_PROJECT;
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
    const secrets = {
      dbUrl: await getSecret('database-url'),
      flaskSecretKey: await getSecret('flask-secret-key'),
      meshyApiKey: await getSecret('meshy-api-key')
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
