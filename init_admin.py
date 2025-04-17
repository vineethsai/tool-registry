#!/usr/bin/env python3
"""
Database initialization script to ensure the admin agent exists.
This script can be run manually or as part of the container startup process.
"""

import os
import sys
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from tool_registry.models.agent import Agent
from tool_registry.core.database import Base

def init_admin_agent():
    """Initialize the database and create admin agent if it doesn't exist."""
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./data/tool_registry.db")
    
    # Connect to the database
    print(f"Connecting to database: {database_url}")
    engine = create_engine(database_url)
    
    try:
        # Check database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("Database connection successful")
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Database tables created or verified")
        
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if admin agent exists
        admin_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        admin_agent = session.query(Agent).filter(Agent.agent_id == admin_id).first()
        
        if not admin_agent:
            print(f"Creating admin agent with ID: {admin_id}")
            admin_agent = Agent(
                agent_id=admin_id,
                name="Admin Agent",
                description="System administrator",
                roles=["admin", "tool_publisher", "policy_admin"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            session.add(admin_agent)
            session.commit()
            print("Admin agent created successfully")
        else:
            print(f"Admin agent already exists with ID: {admin_id}")
        
        # Create test admin if in test mode
        if os.environ.get("TEST_MODE", "false").lower() == "true":
            test_id = uuid.UUID('00000000-0000-0000-0000-000000000003')
            test_agent = session.query(Agent).filter(Agent.agent_id == test_id).first()
            
            if not test_agent:
                print(f"Creating test agent with ID: {test_id}")
                test_agent = Agent(
                    agent_id=test_id,
                    name="Test Agent",
                    description="Test agent for development and testing",
                    roles=["admin", "tool_publisher", "policy_admin"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    is_active=True
                )
                session.add(test_agent)
                session.commit()
                print("Test agent created successfully")
            else:
                print(f"Test agent already exists with ID: {test_id}")
                
        session.close()
        return True
        
    except SQLAlchemyError as e:
        print(f"Database initialization error: {e}")
        return False

if __name__ == "__main__":
    success = init_admin_agent()
    sys.exit(0 if success else 1) 