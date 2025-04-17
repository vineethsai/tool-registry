#!/bin/bash
# build_release.sh - Script to build and tag a new Docker release of Tool Registry

set -e  # Exit on any error

VERSION="2.0.1"
IMAGE_NAME="tool-registry"
REGISTRY="localhost"  # Change this to your Docker registry if needed

echo "Building Tool Registry version $VERSION..."

# Build the Docker image
docker build -t $IMAGE_NAME:$VERSION .

# Tag with latest as well
docker tag $IMAGE_NAME:$VERSION $IMAGE_NAME:latest

# Tag with registry if specified
if [ "$REGISTRY" != "localhost" ]; then
    docker tag $IMAGE_NAME:$VERSION $REGISTRY/$IMAGE_NAME:$VERSION
    docker tag $IMAGE_NAME:$VERSION $REGISTRY/$IMAGE_NAME:latest
    
    echo "Pushing to registry $REGISTRY..."
    docker push $REGISTRY/$IMAGE_NAME:$VERSION
    docker push $REGISTRY/$IMAGE_NAME:latest
fi

echo "Testing the Docker image..."
docker-compose -f docker-compose.yml up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Test the API
echo "Testing API health endpoint..."
curl -s http://localhost:8000/health | grep -q "status" && echo "Health check successful" || echo "Health check failed"

# Run end-to-end test for comprehensive API testing
echo "Running comprehensive API endpoint tests..."
docker exec -it tool-registry-app python test_all_endpoints.py

echo ""
echo "Tool Registry version $VERSION has been built and tagged."
echo "To run the application:"
echo "  docker-compose up -d"
echo ""
echo "To check the logs:"
echo "  docker-compose logs -f app" 