#!/bin/bash
set -e

echo "🚀 Building and starting the Tool Registry application..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Please start Docker and try again."
  exit 1
fi

# Build and start the containers
echo "🔨 Building and starting Docker containers..."
docker-compose build
docker-compose up -d

# Wait for the API to be ready
echo "⏳ Waiting for the API to be ready..."
until $(curl --output /dev/null --silent --head --fail http://localhost:8000/health); do
  printf '.'
  sleep 5
done

echo ""
echo "✅ Tool Registry is now running!"
echo "📊 Frontend: http://localhost"
echo "🔌 API: http://localhost:8000"
echo "📚 Documentation: http://localhost:9000"
echo ""
echo "To stop the application, run: docker-compose down" 