"""
Setup script to configure environment variables for Cloud Run.
"""
import os
import subprocess
import argparse

# Default values based on the detected environment
DEFAULT_ENV = {
    "GOOGLE_CLOUD_PROJECT": "project-2-450420",
    "GCS_BUCKET_NAME": "project-2-450420-images",
    "STORAGE_BUCKET": "project-2-450420-images",
}

def setup_cloud_run_env(service_name):
    """Set up environment variables for a Cloud Run service."""
    print(f"Setting up environment variables for Cloud Run service '{service_name}'...")
    
    # Get current environment variables
    try:
        result = subprocess.run(
            ['gcloud', 'run', 'services', 'describe', service_name, '--format=json'],
            capture_output=True, text=True, check=True
        )
        import json
        service_info = json.loads(result.stdout)
        current_env = {}
        try:
            for env in service_info['spec']['template']['spec']['containers'][0]['env']:
                current_env[env['name']] = env['value']
        except (KeyError, IndexError):
            print("Could not parse current environment variables.")
    except subprocess.CalledProcessError:
        print("Could not get current service configuration.")
        current_env = {}
    
    # Merge with defaults, keeping existing values
    env_vars = DEFAULT_ENV.copy()
    for key, value in current_env.items():
        if key in env_vars and value:
            env_vars[key] = value
    
    # Build update command
    env_args = []
    for key, value in env_vars.items():
        env_args.append(f"--update-env-vars={key}={value}")
    
    if not env_args:
        print("No environment variables to set.")
        return
        
    # Update the service
    print(f"Setting environment variables: {', '.join(env_vars.keys())}")
    try:
        subprocess.run(['gcloud', 'run', 'services', 'update', service_name, *env_args], check=True)
        print("✅ Environment variables set successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to set environment variables: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Set up Cloud Run environment variables')
    parser.add_argument('service_name', help='Name of the Cloud Run service')
    args = parser.parse_args()
    
    setup_cloud_run_env(args.service_name)
