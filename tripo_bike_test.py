import requests
import time
import os

# Configuration
API_KEY = "tsk_DIkZtKit_eLTK6FYrmnxAil4FtDiGQawzF3Hqogr1bF"  # Your Tripo API key
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Get the directory where the script is running
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Step 1: Upload the image
def upload_image(file_name="bike.jpeg"):
    """Uploads bike.jpeg from the script's directory and returns the image_token."""
    file_path = os.path.join(SCRIPT_DIR, file_name)
    if not os.path.exists(file_path):
        print(f"Error: Image file '{file_name}' not found in {SCRIPT_DIR}")
        exit(1)
    
    url = "https://api.tripo3d.ai/v2/openapi/upload"
    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f, 'image/jpeg')}  # JPEG content type for bike.jpeg
        response = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}"}, files=files)
    response_data = response.json()
    if response.status_code == 200 and response_data.get("code") == 0:
        return response_data["data"]["image_token"]
    else:
        print(f"Error uploading image: {response_data}")
        exit(1)

# Step 2: Start the image-to-3D task
def start_image_to_model(image_token):
    """Starts an image-to-3D task with bike.jpeg and returns the task_id."""
    url = "https://api.tripo3d.ai/v2/openapi/task"
    payload = {
        "type": "image_to_model",
        "file": {
            "type": "jpg",  # Matches bike.jpeg
            "file_token": image_token
        },
        "model_version": "v2.5-20250123"  # Latest version
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    response_data = response.json()
    if response.status_code == 200 and response_data.get("code") == 0:
        return response_data["data"]["task_id"]
    else:
        print(f"Error starting task: {response_data}")
        exit(1)

# Step 3: Check task status
def check_task_status(task_id):
    """Polls the task status until complete and returns the model URL."""
    url = f"https://api.tripo3d.ai/v2/openapi/task/{task_id}"
    while True:
        response = requests.get(url, headers=HEADERS)
        response_data = response.json()
        if response.status_code == 200 and response_data.get("code") == 0:
            status = response_data["data"]["status"]
            print(f"Task status: {status}")
            if status == "success":
                print(f"Full response: {response_data}")  # Keep for debugging
                return response_data["data"]["result"]["pbr_model"]["url"]  # Correct field
            elif status in ["failed", "canceled"]:
                print(f"Task failed or canceled: {response_data}")
                exit(1)
        else:
            print(f"Error checking status: {response_data}")
            exit(1)
        time.sleep(10)  # Poll every 10 seconds

# Step 4: Download the model
def download_model(model_url, output_file_name="bike_model.glb"):
    """Downloads the 3D model to the script's directory as bike_model.glb."""
    output_path = os.path.join(SCRIPT_DIR, output_file_name)
    response = requests.get(model_url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Model downloaded to {output_path}")
    else:
        print(f"Error downloading model: {response.status_code}")
        exit(1)

# Main function
def main():
    """Executes the full Tripo API workflow for bike.jpeg."""
    # Upload bike.jpeg
    image_token = upload_image()
    print(f"Image uploaded, token: {image_token}")

    # Start image-to-3D task
    task_id = start_image_to_model(image_token)
    print(f"Task started, ID: {task_id}")

    # Check task status and get model URL
    model_url = check_task_status(task_id)

    # Download the model
    download_model(model_url)

if __name__ == "__main__":
    main()