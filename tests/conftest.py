"""Test fixtures for the Tool Registry system."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tool_registry.core.database import Base
from tool_registry.models import Agent, Tool, Policy, Credential, AccessLog

@pytest.fixture(scope="session")
def test_db():
    """Create a test database session."""
    # Create engine with SQLite memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def test_agent(test_db):
    """Create a test agent."""
    agent = Agent(
        agent_id=uuid4(),
        name="Test Agent",
        description="Test agent for unit tests",
        roles=["user"]
    )
    test_db.add(agent)
    test_db.commit()
    return agent

@pytest.fixture
def test_admin_agent(test_db):
    """Create a test admin agent."""
    agent = Agent(
        agent_id=uuid4(),
        name="Test Admin",
        description="Test admin agent",
        roles=["admin"]
    )
    test_db.add(agent)
    test_db.commit()
    return agent

@pytest.fixture
def test_tool(test_db, test_admin_agent):
    """Create a test tool."""
    tool = Tool(
        tool_id=uuid4(),
        name="Test Tool",
        description="Test tool for unit tests",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={},
        params={},
        version="1.0.0",
        owner=test_admin_agent,
        owner_id=test_admin_agent.agent_id
    )
    test_db.add(tool)
    test_db.commit()
    return tool

@pytest.fixture
def test_policy(test_db, test_tool, test_admin_agent):
    """Create a test policy."""
    policy = Policy(
        policy_id=uuid4(),
        name="Test Policy",
        description="Test policy for unit tests",
        rules={
            "roles": ["user"],
            "allowed_scopes": ["read"]
        },
        created_by=test_admin_agent.agent_id
    )
    test_db.add(policy)
    test_db.commit()
    return policy

@pytest.fixture
def test_credential(test_db, test_agent, test_tool):
    """Create a test credential."""
    credential = Credential(
        credential_id=uuid4(),
        agent_id=test_agent.agent_id,
        tool_id=test_tool.tool_id,
        token="test-token",
        scope="read",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    test_db.add(credential)
    test_db.commit()
    return credential 