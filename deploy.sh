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




