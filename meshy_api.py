"""
Meshy API client for converting images to 3D models.
Based on the provided FastAPI reference implementation.
"""
import os
import time
import base64
import requests
import logging
from gcp_secrets import get_secret_or_env

logger = logging.getLogger(__name__)

# Get the API key from secrets or environment variables
MESHY_API_KEY = None

def init_api():
    """Initialize the Meshy API client with API key."""
    global MESHY_API_KEY
    
    # Try to get API key from secrets or environment
    MESHY_API_KEY = get_secret_or_env('meshy-api-key', 'MESHY_API_KEY')
    
    if not MESHY_API_KEY:
        logger.error("MESHY_API_KEY not found in secrets or environment")
        return False
    return True

def get_headers():
    """Get API request headers with authorization."""
    if not MESHY_API_KEY and not init_api():
        raise ValueError("Meshy API key not configured")
        
    return {
        "Authorization": f"Bearer {MESHY_API_KEY}", 
        "Content-Type": "application/json"
    }

def image_to_data_uri(image_bytes):
    """Convert image bytes to data URI."""
    return f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

def upload_image_to_3d(image_path, settings=None):
    """
    Upload an image to Meshy API for 3D conversion.
    
    Args:
        image_path: Path to the image file
        settings: Dictionary of settings for conversion
        
    Returns:
        task_id: The task ID for tracking conversion progress
        error: Error message if any
    """
    if not os.path.exists(image_path):
        return None, f"Image file not found: {image_path}"
        
    try:
        # Read the image file
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        # Convert to data URI
        image_data_uri = image_to_data_uri(image_bytes)
        
        # Default settings if none provided
        if settings is None:
            settings = {
                "enable_pbr": False,
                "should_remesh": True, 
                "should_texture": True
            }
            
        # Prepare the request payload
        payload = {
            "image_url": image_data_uri,
            **settings
        }
        
        # Make the API call
        response = requests.post(
            "https://api.meshy.ai/openapi/v1/image-to-3d",
            json=payload, 
            headers=get_headers()
        )
        response.raise_for_status()
        
        # Parse the response
        task_data = response.json()
        task_id = task_data.get("result")
        
        if not task_id:
            logger.error("Meshy API did not return a task ID")
            return None, "Meshy API did not return a task ID"
            
        logger.info(f"Successfully submitted image to Meshy API. Task ID: {task_id}")
        return task_id, None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Meshy API request error: {e}")
        return None, f"Meshy API request error: {str(e)}"
    except Exception as e:
        logger.error(f"Error uploading image to Meshy API: {e}")
        return None, str(e)

def check_task_status(task_id):
    """
    Check the status of a conversion task.
    
    Args:
        task_id: The task ID to check
        
    Returns:
        status: The status of the task (processing, completed, failed)
        result_url: URL to the 3D model if completed
        error: Error message if any
    """
    try:
        # Make the API call to check status
        response = requests.get(
            f"https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}",
            headers=get_headers()
        )
        response.raise_for_status()
        
        # Parse the response
        task_json = response.json()
        status_ = task_json.get("status")
        
        # Map Meshy API status to our status format
        if status_ == "SUCCEEDED":
            # Get the model URL
            model_urls = task_json.get("model_urls", {})
            glb_url = model_urls.get("glb")
            
            if not glb_url:
                logger.error("No GLB URL found in Meshy response")
                return "failed", None, "No GLB URL found in Meshy response"
                
            return "completed", glb_url, None
            
        elif status_ in ["FAILED", "CANCELED"]:
            return "failed", None, f"Meshy task {status_}"
            
        # Still processing
        return "processing", None, None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking task status: {e}")
        return "failed", None, f"API Error: {str(e)}"
        
    except Exception as e:
        logger.error(f"Error checking task status: {e}")
        return "failed", None, str(e)

def download_model(url, save_path):
    """
    Download a 3D model from URL.
    
    Args:
        url: URL of the model to download
        save_path: Path where to save the model
        
    Returns:
        success: True if download was successful
        error: Error message if any
    """
    try:
        # Download the model
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save to file
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return True, None
        
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return False, str(e)
