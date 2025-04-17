#!/bin/bash
set -e

echo "🔍 Checking admin agent in the database..."

# Check if container is running
if ! docker ps | grep -q tool-registry-app; then
  echo "❌ The tool-registry-app container is not running. Start it with docker-compose up -d"
  exit 1
fi

# Run the SQL query directly in the container to check for the admin agent
echo "Checking for admin agent with ID 00000000-0000-0000-0000-000000000001..."
ADMIN_EXISTS=$(docker exec -it tool-registry-db psql -U postgres -d toolregistry -t -c "SELECT COUNT(*) FROM agents WHERE agent_id = '00000000-0000-0000-0000-000000000001'::uuid;")

# Trim whitespace
ADMIN_EXISTS=$(echo $ADMIN_EXISTS | xargs)

if [ "$ADMIN_EXISTS" -eq "0" ]; then
  echo "Admin agent not found. Creating it now..."
  
  # Create admin agent
  docker exec -it tool-registry-db psql -U postgres -d toolregistry -c "
  INSERT INTO agents (agent_id, name, description, roles, created_at, updated_at, is_active) 
  VALUES ('00000000-0000-0000-0000-000000000001'::uuid, 'Admin Agent', 'System administrator', 
  ARRAY['admin', 'tool_publisher', 'policy_admin'], NOW(), NOW(), TRUE)
  ON CONFLICT (agent_id) DO NOTHING;
  "
  
  echo "✅ Admin agent created successfully."
else
  echo "✅ Admin agent already exists."
fi

# Check for test agent with ID 00000000-0000-0000-0000-000000000003
echo "Checking for test agent with ID 00000000-0000-0000-0000-000000000003..."
TEST_EXISTS=$(docker exec -it tool-registry-db psql -U postgres -d toolregistry -t -c "SELECT COUNT(*) FROM agents WHERE agent_id = '00000000-0000-0000-0000-000000000003'::uuid;")

# Trim whitespace
TEST_EXISTS=$(echo $TEST_EXISTS | xargs)

if [ "$TEST_EXISTS" -eq "0" ]; then
  echo "Test agent not found. Creating it now..."
  
  # Create test agent
  docker exec -it tool-registry-db psql -U postgres -d toolregistry -c "
  INSERT INTO agents (agent_id, name, description, roles, created_at, updated_at, is_active) 
  VALUES ('00000000-0000-0000-0000-000000000003'::uuid, 'Test Agent', 'Test agent for development', 
  ARRAY['admin', 'tool_publisher', 'policy_admin'], NOW(), NOW(), TRUE)
  ON CONFLICT (agent_id) DO NOTHING;
  "
  
  echo "✅ Test agent created successfully."
else
  echo "✅ Test agent already exists."
fi

echo "✅ Agent verification complete." 