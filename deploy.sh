#!/bin/bash

# Tool Registry Deployment Script
# Usage: ./deploy.sh [docker|dev]
#   docker - Deploy using Docker Compose
#   dev    - Run the development server

set -e

MODE=${1:-dev}  # Default to dev mode if not specified

echo "Tool Registry Deployment"
echo "========================"

# Create a venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing requirements..."
pip install -q -e .
pip install -q python-dotenv uvicorn requests

# Make scripts executable
chmod +x run_api.py test_api.py

case $MODE in
    docker)
        echo "Starting Docker deployment..."
        docker-compose down || echo "No containers to stop"
        docker-compose up -d
        echo "Docker containers started"
        echo "API is available at http://localhost:8000"
        ;;
    dev)
        echo "Starting development server..."
        ./run_api.py &
        SERVER_PID=$!
        echo "API server started with PID: $SERVER_PID"
        echo "API is available at http://localhost:8000"
        
        # Wait for server to start
        echo "Waiting for server to start..."
        sleep 3
        
        # Run tests
        echo "Running tests..."
        ./test_api.py
        
        # Cleanup
        echo "Stopping server..."
        kill $SERVER_PID
        ;;
    *)
        echo "Unknown mode: $MODE"
        echo "Usage: ./deploy.sh [docker|dev]"
        exit 1
        ;;
esac

echo "Deployment completed" 