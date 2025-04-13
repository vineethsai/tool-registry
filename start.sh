#!/bin/bash
set -e

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

# Run a simple Python script to initialize the database tables
echo "Initializing database tables..."
python -c "
from tool_registry.core.database import Base, engine
from tool_registry.models.agent import Agent
from tool_registry.models.tool import Tool
from tool_registry.models.policy import Policy
from tool_registry.models.credential import Credential
from tool_registry.models.access_log import AccessLog
from tool_registry.models.tool_metadata import ToolMetadata
import uuid
from datetime import datetime

# Create all tables
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')

# Create a session to work with
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

# Check if admin agent exists, create if not
admin_exists = session.query(Agent).filter(Agent.name == 'Admin Agent').first()
if not admin_exists:
    print('Creating admin agent...')
    admin_agent = Agent(
        agent_id=uuid.UUID('00000000-0000-0000-0000-000000000001'),
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

# Commit and close
session.close()
"

# Start the application
exec uvicorn tool_registry.api.app:app --host 0.0.0.0 --port 8000 "$@" 