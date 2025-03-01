from fastapi import FastAPI, File, UploadFile, Form
import requests
import os
import base64
import time
from dotenv import load_dotenv  # For loading environment variables

# Load environment variables from .env file
load_dotenv()

# Define FastAPI app
app = FastAPI()

# Load API Key from environment variable; if not found, prompt the user
API_KEY = os.getenv("MESHY_API_KEY")
if not API_KEY:
    print("Warning: API Key not found. Please set MESHY_API_KEY environment variable.")
    API_KEY = input("Enter your API key: ")

# Define request headers for the Meshy API
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Set the custom directory where the downloaded 3D model will be saved
SAVE_DIR = "/users/apple/Downloads"  # Change as needed for your OS
os.makedirs(SAVE_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"message": "Backend is running! Visit /docs for API documentation."}

def image_to_data_uri(image_bytes: bytes) -> str:
    """
    Convert image bytes to a Base64 Data URI.
    """
    base64_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_data}"

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), username: str = Form("guest")):
    print(f"Received file: {file.filename}, Type: {file.content_type}, User: {username}")
    try:
        # Read the uploaded file and convert it to a Data URI
        file_bytes = await file.read()
        image_data_uri = image_to_data_uri(file_bytes)
        
        # Build the payload (using enable_pbr=False as per second code)
        payload = {
            "image_url": image_data_uri,
            "enable_pbr": False,
            "should_remesh": True,
            "should_texture": True
        }
        response = requests.post("https://api.meshy.ai/openapi/v1/image-to-3d", json=payload, headers=HEADERS)
        response.raise_for_status()
        task_data = response.json()
        task_id = task_data.get("result")
        if not task_id:
            return {"error": "Task ID not received", "details": task_data}
        print(f"Task Created: {task_id}")
        
        # Poll for task completion
        while True:
            time.sleep(30)  # Wait 10 seconds before checking status again
            task_response = requests.get(f"https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}", headers=HEADERS)
            task_status = task_response.json()
            status = task_status.get("status")
            progress = task_status.get("progress", 0)
            print(f"Task Status: {status}, Progress: {progress}%")
            
            if status == "SUCCEEDED":
                # Get the GLB file URL
                model_urls = task_status.get("model_urls", {})
                glb_url = model_urls.get("glb")
                if not glb_url:
                    return {"error": "3D model URL not found", "details": task_status}
                print(f"3D Model Ready: {glb_url}")
                
                # Download the GLB file and save it to the custom directory
                base_filename = os.path.splitext(file.filename)[0]
                output_filename = os.path.join(SAVE_DIR, f"{base_filename}_{int(time.time())}.glb")
                print(f"Downloading {glb_url} to {output_filename} ...")
                
                glb_response = requests.get(glb_url, stream=True)
                glb_response.raise_for_status()
                with open(output_filename, "wb") as f:
                    for chunk in glb_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Download complete! File saved at {output_filename}")
                return {"model_file": output_filename}
            elif status in ["FAILED", "CANCELED"]:
                return {"error": f"Task {status}", "details": task_status}
    except Exception as e:
        print("Error processing file:", str(e))
        return {"error": "Internal Server Error", "details": str(e)}