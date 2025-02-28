import requests
import base64
import time
import os

# Load API key
API_KEY = os.getenv("MESHY_API_KEY", "msy_gXlokg8zy7u2PhYDva8gSGb4S9PTNJaiPMx7")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Convert local image to Data URI
def image_to_data_uri(image_path):
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
    base64_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_data}"

# Test Meshy API
def test_meshy_api(image_path):
    image_data_uri = image_to_data_uri(image_path)
    payload = {
        "image_url": image_data_uri,
        "enable_pbr": False,
        "should_remesh": True,
        "should_texture": True
    }
    
    print("Creating task...")
    response = requests.post("https://api.meshy.ai/openapi/v1/image-to-3d", json=payload, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return
    
    task_data = response.json()
    task_id = task_data.get("result")
    if not task_id:
        print("No task ID received.")
        return
    
    print(f"Task ID: {task_id}")
    
    while True:
        time.sleep(10)
        task_response = requests.get(f"https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}", headers=HEADERS)
        if task_response.status_code != 200:
            print(f"Polling error: {task_response.text}")
            break
        
        task_status = task_response.json()
        status = task_status.get("status")
        progress = task_status.get("progress", 0)
        print(f"Status: {status}, Progress: {progress}%")
        
        if status == "SUCCEEDED":
            model_urls = task_status.get("model_urls", {})
            glb_url = model_urls.get("glb")
            if glb_url:
                print(f"Model URL: {glb_url}")
                # Optionally download the model
                with open("output.glb", "wb") as f:
                    f.write(requests.get(glb_url).content)
                print("Model downloaded as output.glb")
            break
        elif status in ["FAILED", "CANCELED"]:
            print(f"Task {status}")
            break

if __name__ == "__main__":
    # Replace with a local image path
    test_meshy_api("test_image.jpg")