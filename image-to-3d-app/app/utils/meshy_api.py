import requests
import os

class MeshyAPI:
    def __init__(self):
        self.api_key = os.getenv('MESHY_API_KEY')
        self.base_url = 'https://api.meshy.com/v1'

    def convert_image(self, image_path):
        url = f"{self.base_url}/convert"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        files = {'file': open(image_path, 'rb')}
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()