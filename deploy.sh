#!/bin/bash

# Stop on errors
set -e

echo "Current working directory: $(pwd)"
echo "Attempting to change directory to ~/UMOD"
cd ~/UMOD
echo "Changed directory successfully"

# Pull latest changes from main branch
git fetch origin main
git reset --hard origin/main

# Stop and remove old container (optional)
docker stop your_app_container || true
docker rm your_app_container || true

# Remove old Docker image
docker rmi your_app_image || true

# Build the new Docker image
docker build -t your_app_image .

# Run the container using the new image
docker run -d -p 8000:8000 --name your_app_container your_app_image

echo "Deployment completed!"



