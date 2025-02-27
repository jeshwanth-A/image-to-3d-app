"""
Helper module to access Google Cloud Secret Manager secrets.
"""
import os
import logging
from google.cloud import secretmanager

# Configure logging
logger = logging.getLogger(__name__)

# Project ID is needed for accessing Secret Manager
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

# Initialize the Secret Manager client
client = None
try:
    client = secretmanager.SecretManagerServiceClient()
    logger.info("Secret Manager client initialized")
except Exception as e:
    logger.error(f"Failed to initialize Secret Manager client: {e}")

def get_secret(secret_id, version_id="latest"):
    """
    Access the secret with the given name and version.
    
    Args:
        secret_id: Name of the secret to access
        version_id: Version of the secret (defaults to "latest")
        
    Returns:
        The secret payload as a string or None if access fails
    """
    # If client initialization failed, return None
    if not client:
        logger.error("Secret Manager client not available")
        return None
        
    # If project ID is not available, return None
    if not PROJECT_ID:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
        return None
        
    try:
        # Build the resource name
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
        
        # Access the secret version
        response = client.access_secret_version(request={"name": name})
        
        # Return the decoded payload
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}")
        return None

# Cache for secrets to avoid repeated calls to Secret Manager
_secret_cache = {}

def get_secret_or_env(secret_id, env_var_name=None, default=None):
    """
    Get a secret from Secret Manager, falling back to environment variable, then default.
    
    Args:
        secret_id: Name of the secret in Secret Manager
        env_var_name: Name of the environment variable (defaults to same as secret_id)
        default: Default value if secret and environment variable are not available
        
    Returns:
        The secret value as a string, or the default
    """
    if env_var_name is None:
        env_var_name = secret_id.replace('-', '_').upper()
        
    # Check cache first
    if secret_id in _secret_cache:
        return _secret_cache[secret_id]
    
    # Try Secret Manager
    secret_value = get_secret(secret_id)
    
    # If Secret Manager failed, try environment variable
    if secret_value is None:
        secret_value = os.environ.get(env_var_name)
        logger.info(f"Using environment variable {env_var_name} instead of Secret Manager")
    else:
        logger.info(f"Successfully retrieved secret {secret_id} from Secret Manager")
        # Cache the secret
        _secret_cache[secret_id] = secret_value
        
    # If both failed, use default
    if secret_value is None:
        logger.warning(f"Falling back to default value for {secret_id}")
        return default
        
    return secret_value
