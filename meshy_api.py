"""
Meshy API client for 3D model conversion.

This module handles all communication with the Meshy API for converting 
images to 3D models.
"""
import os
import requests
import logging
import json
import time
import base64
from gcp_secrets import get_secret_or_env

logger = logging.getLogger(__name__)

# Meshy API configuration
API_BASE_URL = "https://api.meshy.ai/v1"
MESHY_API_KEY = None

def init_api():
    """Initialize the API client with the API key."""
    global MESHY_API_KEY
    MESHY_API_KEY = get_secret_or_env('meshy-api-key', 'MESHY_API_KEY')
    if not MESHY_API_KEY:
        logger.error("Meshy API key not found!")
        return False
    return True

def get_headers():
    """Get the request headers with authentication."""
    return {
        "Authorization": f"Bearer {MESHY_API_KEY}",
        "Content-Type": "application/json"
    }

def upload_image_to_3d(image_path, settings=None):
    """
    Upload an image to Meshy API for 3D conversion.
    
    Args:
        image_path: Path to the image file
        settings: Dictionary of settings for the Meshy API
        
    Returns:
        task_id: The task ID for tracking conversion progress
        error: Error message if any
    """
    if not init_api():
        return None, "API key not configured"
    
    try:
        # Read the image file as base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Default settings if none provided
        if settings is None:
            settings = {
                "promptText": "High quality detailed 3D model",
                "negativePromptText": "low quality, bad geometry",
                "taskType": "text-to-3d"  # or 'image-to-3d' based on API docs
            }
        
        # Prepare request payload
        payload = {
            "image": f"data:image/jpeg;base64,{image_data}",
            **settings
        }
        
        # Make API call
        response = requests.post(
            f"{API_BASE_URL}/image-to-3d",
            headers=get_headers(),
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None, f"API Error: {response.status_code}"
        
        # Parse response
        result = response.json()
        task_id = result.get("taskId")
        
        if not task_id:
            logger.error("No task ID returned from API")
            return None, "No task ID returned"
        
        logger.info(f"Successfully submitted image to Meshy API. Task ID: {task_id}")
        return task_id, None
        
    except Exception as e:
        logger.error(f"Error uploading image to Meshy API: {e}")
        return None, str(e)

def check_task_status(task_id):
    """
    Check the status of a task with the Meshy API.
    
    Args:
        task_id: The task ID to check
        
    Returns:
        status: The status of the task (processing, completed, failed)
        result_url: URL to the 3D model if completed
        error: Error message if any
    """
    if not init_api():
        return "failed", None, "API key not configured"
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/tasks/{task_id}",
            headers=get_headers()
        )
        
        if response.status_code != 200:
            logger.error(f"API Error checking task: {response.status_code} - {response.text}")
            return "failed", None, f"API Error: {response.status_code}"
        
        result = response.json()
        status = result.get("status", "unknown")
        
        # Handle different statuses
        if status == "completed":
            # Get the download URL for the 3D model
            model_url = result.get("resultUrl")
            if not model_url:
                return "failed", None, "No result URL in completed task"
            return "completed", model_url, None
        elif status == "failed":
            error_message = result.get("errorMessage", "Unknown error")
            return "failed", None, error_message
        else:
            # Still processing
            return "processing", None, None
            
    except Exception as e:
        logger.error(f"Error checking task status: {e}")
        return "failed", None, str(e)

def download_model(result_url, save_path):
    """
    Download a 3D model from the provided URL.
    
    Args:
        result_url: URL to the 3D model
        save_path: Path to save the downloaded model
        
    Returns:
        success: True if download was successful
        error: Error message if any
    """
    try:
        response = requests.get(result_url, stream=True)
        
        if response.status_code != 200:
            return False, f"Download failed with status {response.status_code}"
        
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True, None
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return False, str(e)

# Example usage:
# task_id, error = upload_image_to_3d("path/to/image.jpg")
# status, result_url, error = check_task_status(task_id)
# if status == "completed":
#     download_model(result_url, "path/to/save/model.glb")
