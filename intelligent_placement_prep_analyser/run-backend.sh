#!/bin/bash

# Start Backend Server on port 8003
echo "Starting Backend Server on port 8003..."
cd "$(dirname "$0")/backend"

# Activate virtual environment
source venv/bin/activate 2>/dev/null || echo "Virtual environment not found. Install dependencies with: source venv/bin/activate && pip install -r requirements.txt"

# Run the backend
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
