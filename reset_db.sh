#!/bin/bash
set -e

echo "🔄 Resetting the Tool Registry database..."

# Stop containers if they're running
echo "Stopping containers..."
docker-compose down

# Remove database volume
echo "Removing database volume..."
docker volume rm tool-registry_postgres_data || true

# Start containers again with TEST_MODE enabled
echo "Starting containers with TEST_MODE enabled..."
TEST_MODE=true docker-compose up -d

echo "⏳ Waiting for initialization..."
sleep 20  # Increased wait time to ensure proper initialization

# Check if the API is running
echo "Checking if the API is running..."
curl -s http://localhost:8000/health || echo "API not yet available, waiting longer..."
sleep 10

echo "✅ Database reset complete!"
echo "The application is now running with a fresh database." 