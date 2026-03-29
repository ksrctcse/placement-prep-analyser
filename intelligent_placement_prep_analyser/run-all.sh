#!/bin/bash

# Start all services
echo "Starting Placement Prep Analyser Services"
echo "=========================================="
echo ""
echo "Frontend will run on:  http://localhost:5175"
echo "Backend API on:        http://localhost:8003"
echo "Swagger Docs on:       http://localhost:8003/docs"
echo "ReDoc on:              http://localhost:8003/redoc"
echo ""

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start Backend
echo "Starting Backend Server..."
bash "$SCRIPT_DIR/run-backend.sh" &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start Frontend
echo "Starting Frontend Server..."
bash "$SCRIPT_DIR/run-frontend.sh" &
FRONTEND_PID=$!

echo ""
echo "Servers started! Press Ctrl+C to stop all services."
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
