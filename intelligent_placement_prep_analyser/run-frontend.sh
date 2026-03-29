#!/bin/bash

# Start Frontend Server on port 5175
echo "Starting Frontend Server on port 5175..."
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

# Run the frontend
npm run dev
