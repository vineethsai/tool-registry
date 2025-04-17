#!/bin/bash
set -e

# Install email-validator to ensure it's available
pip install --no-cache-dir email-validator==2.1.0
echo "Installed email-validator"

# Wait for PostgreSQL if using PostgreSQL
if [[ $DATABASE_URL == postgresql* ]]; then
  echo "Waiting for PostgreSQL..."
  
  # Extract host and port from DATABASE_URL
  DB_HOST=$(echo $DATABASE_URL | awk -F[@//] '{print $4}' | awk -F[:] '{print $1}')
  DB_PORT=$(echo $DATABASE_URL | awk -F[@//] '{print $4}' | awk -F[:] '{print $2}' | awk -F[/] '{print $1}')
  
  # Default to 5432 if port not specified
  DB_PORT=${DB_PORT:-5432}
  
  # Wait for PostgreSQL to be ready
  until nc -z $DB_HOST $DB_PORT; do
    echo "PostgreSQL not available yet - sleeping 1s"
    sleep 1
  done
  
  echo "PostgreSQL is up - continuing"
fi

# Create necessary directories for SQLite
if [[ $DATABASE_URL == sqlite* ]]; then
  mkdir -p /app/data
  touch /app/data/tool_registry.db
  echo "SQLite database path initialized"
fi

# Run initialization directly in the script
echo "Initializing database and creating admin agents..."

# Initialize the database directly in the script
if [ -f "/app/init_admin.py" ]; then
  echo "Using init_admin.py script..."
  python /app/init_admin.py
  
  # If the initialization fails, retry with a delay
  if [ $? -ne 0 ]; then
    echo "Initial database setup failed, retrying in 5 seconds..."
    sleep 5
    python /app/init_admin.py
  fi
else
  echo "init_admin.py not found, using inline initialization..."
  python -c "
from tool_registry.core.database import Base, engine
from tool_registry.models.agent import Agent
import uuid
from datetime import datetime
from sqlalchemy.orm import sessionmaker

# Create all tables
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')

# Create a session to work with
Session = sessionmaker(bind=engine)
session = Session()

# Check if admin agent exists, create if not
admin_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
admin_agent = session.query(Agent).filter(Agent.agent_id == admin_id).first()
if not admin_agent:
    print('Creating admin agent...')
    admin_agent = Agent(
        agent_id=admin_id,
        name='Admin Agent',
        description='System administrator',
        roles=['admin', 'tool_publisher', 'policy_admin'],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_active=True
    )
    session.add(admin_agent)
    session.commit()
    print('Admin agent created successfully')
else:
    print('Admin agent already exists')

# Create test agent if in test mode
test_mode = '${TEST_MODE}'.lower() == 'true'
if test_mode:
    test_id = uuid.UUID('00000000-0000-0000-0000-000000000003')
    test_agent = session.query(Agent).filter(Agent.agent_id == test_id).first()
    if not test_agent:
        print('Creating test agent...')
        test_agent = Agent(
            agent_id=test_id,
            name='Test Agent',
            description='Test agent for development and testing',
            roles=['admin', 'tool_publisher', 'policy_admin'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        session.add(test_agent)
        session.commit()
        print('Test agent created successfully')
    else:
        print('Test agent already exists')

# Commit and close
session.close()
"
fi

# Start the application
exec uvicorn tool_registry.api.app:app --host 0.0.0.0 --port 8000 "$@" 