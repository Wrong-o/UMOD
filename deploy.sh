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

# Ensure proper permissions on static directory
sudo chown -R www-data:www-data /app/app/static
sudo chmod -R 755 /app/app/static

# Rebuild and restart containers
docker-compose build
docker-compose up -d