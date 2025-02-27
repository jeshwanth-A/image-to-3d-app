#!/bin/bash

# Set variables - replace these with your values
PROJECT_ID="your-google-cloud-project-id"
REGION="us-central1"  # Cloud Run region
SERVICE_NAME="image-to-3d-app"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build the container
echo "Building container image..."
gcloud builds submit --tag "$IMAGE_NAME" .

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 300s \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

echo "Deployment complete!"

# Show the service URL
gcloud run services describe "$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --format="value(status.url)"
