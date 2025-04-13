import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID, uuid4
from pydantic import ValidationError, HttpUrl
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from tool_registry.models import (
    ToolMetadata,
    Tool,
    Agent,
    Policy,
    Credential,
    AccessLog
)
from tool_registry.core.database import Base

@pytest.fixture(scope="function")
def test_db():
    """Create a test database and yield a session instance."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()  # Ensure any failed transaction is rolled back
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_tool_metadata_model(test_db):
    """Test the ToolMetadata model validation."""
    # Create a tool first
    owner = Agent(
        agent_id=uuid4(),
        name="Test Owner",
        description="Test owner agent",
        roles=["owner"]
    )
    
    test_db.add(owner)
    test_db.flush()
    
    tool = Tool(
        tool_id=uuid4(),
        name="Test Tool",
        description="Test tool for unit tests",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={"header_name": "X-API-Key"},
        params={"text": {"type": "string", "required": True}},
        version="1.0.0",
        owner=owner,
        owner_id=owner.agent_id
    )
    
    test_db.add(tool)
    test_db.flush()
    
    # Valid metadata
    valid_metadata = ToolMetadata(
        tool_id=tool.tool_id,
        schema_version="1.0",
        inputs={"text": {"type": "string"}},
        outputs={"result": {"type": "string"}}
    )
    test_db.add(valid_metadata)
    test_db.commit()
    
    assert valid_metadata.tool_id == tool.tool_id
    assert valid_metadata.schema_version == "1.0"
    assert "text" in valid_metadata.inputs
    assert "result" in valid_metadata.outputs
    assert isinstance(valid_metadata.created_at, datetime)
    assert isinstance(valid_metadata.updated_at, datetime)
    
    # Optional documentation URL
    metadata_with_docs = ToolMetadata(
        tool_id=tool.tool_id,
        schema_version="1.0",
        inputs={"text": {"type": "string"}},
        outputs={"result": {"type": "string"}},
        documentation_url="https://docs.example.com"
    )
    test_db.add(metadata_with_docs)
    test_db.commit()
    
    assert metadata_with_docs.documentation_url == "https://docs.example.com"
    assert isinstance(metadata_with_docs.created_at, datetime)

    # Test that NULL constraint is enforced by SQLAlchemy
    # This is a different approach since we can't use pydantic validation
    with pytest.raises(Exception):
        invalid_metadata = ToolMetadata(
            schema_version="1.0"
            # Missing tool_id which is NOT NULL
        )
        test_db.add(invalid_metadata)
        test_db.flush()

def test_tool_model(test_db):
    """Test the Tool model validation."""
    # Create an owner agent first
    owner = Agent(
        agent_id=uuid4(),
        name="Test Owner",
        description="Test owner agent",
        roles=["owner"]
    )
    test_db.add(owner)
    test_db.commit()
    
    # Valid tool
    tool_id = uuid4()
    valid_tool = Tool(
        tool_id=tool_id,
        name="Test Tool",
        description="Test tool for unit tests",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={"header_name": "X-API-Key"},
        params={"text": {"type": "string", "required": True}},
        version="1.0.0",
        owner=owner,
        owner_id=owner.agent_id
    )
    test_db.add(valid_tool)
    test_db.commit()
    
    assert valid_tool.tool_id == tool_id
    assert valid_tool.name == "Test Tool"
    assert valid_tool.description == "Test tool for unit tests"
    assert valid_tool.api_endpoint == "https://api.example.com/test"
    assert valid_tool.auth_method == "API_KEY"
    assert "header_name" in valid_tool.auth_config
    assert valid_tool.version == "1.0.0"
    assert valid_tool.owner == owner
    assert valid_tool.owner_id == owner.agent_id
    assert isinstance(valid_tool.created_at, datetime)
    assert isinstance(valid_tool.updated_at, datetime)
    
    # Default values
    assert valid_tool.tags == []
    assert valid_tool.allowed_scopes == []
    assert valid_tool.is_active == True
    
    # With metadata
    metadata = ToolMetadata(
        metadata_id=uuid4(),
        tool_id=valid_tool.tool_id,
        schema_version="1.0",
        inputs={"text": {"type": "string"}},
        outputs={"result": {"type": "string"}}
    )
    test_db.add(metadata)
    test_db.commit()
    
    tool_with_metadata = Tool(
        tool_id=uuid4(),
        name="Test Tool",
        description="Test tool with metadata",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={},
        params={},
        version="1.0.0",
        owner=owner,
        owner_id=owner.agent_id,
        tool_metadata_rel=metadata
    )
    test_db.add(tool_with_metadata)
    test_db.commit()
    
    assert tool_with_metadata.tool_metadata_rel == metadata
    assert isinstance(tool_with_metadata.created_at, datetime)

def test_agent_model(test_db):
    """Test the Agent model validation."""
    # Valid agent
    agent_id = uuid4()
    valid_agent = Agent(
        agent_id=agent_id,
        name="Test Agent",
        description="Test agent for unit tests",
        roles=["tester", "user"]
    )
    test_db.add(valid_agent)
    test_db.commit()
    
    assert valid_agent.agent_id == agent_id
    assert valid_agent.name == "Test Agent"
    assert valid_agent.description == "Test agent for unit tests"
    assert "tester" in valid_agent.roles
    assert "user" in valid_agent.roles
    assert isinstance(valid_agent.created_at, datetime)
    assert isinstance(valid_agent.updated_at, datetime)
    assert len(valid_agent.allowed_tools) == 0  # Default empty list
    
    # Optional fields
    assert valid_agent.creator is None
    assert valid_agent.api_key_hash is None
    
    # With allowed tools
    tool_id1 = str(uuid4())
    tool_id2 = str(uuid4())
    agent_with_tools = Agent(
        name="Tool Access Agent",
        allowed_tools=[tool_id1, tool_id2]
    )
    test_db.add(agent_with_tools)
    test_db.commit()
    
    assert len(agent_with_tools.allowed_tools) == 2
    assert tool_id1 in agent_with_tools.allowed_tools
    assert tool_id2 in agent_with_tools.allowed_tools
    assert isinstance(agent_with_tools.created_at, datetime)

def test_policy_model(test_db):
    """Test the Policy model validation."""
    # Create required related objects
    owner = Agent(
        agent_id=uuid4(),
        name="Test Owner",
        description="Test owner",
        roles=["owner"]
    )
    test_db.add(owner)
    test_db.commit()
    
    tool = Tool(
        tool_id=uuid4(),
        name="Test Tool",
        description="Test tool",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={},
        params={},
        version="1.0.0",
        owner=owner,
        owner_id=owner.agent_id
    )
    test_db.add(tool)
    test_db.commit()
    
    # Valid policy
    policy_id = uuid4()
    valid_policy = Policy(
        policy_id=policy_id,
        name="Test Policy",
        description="Test policy for unit tests",
        rules={
            "roles": ["tester", "admin"],
            "allowed_scopes": ["read", "write"]
        },
        created_by=owner.agent_id
    )
    
    # Add the tool to the policy
    valid_policy.tools.append(tool)
    
    test_db.add(valid_policy)
    test_db.commit()
    
    assert valid_policy.policy_id == policy_id
    assert valid_policy.name == "Test Policy"
    assert valid_policy.description == "Test policy for unit tests"
    assert "roles" in valid_policy.rules
    assert "allowed_scopes" in valid_policy.rules
    assert isinstance(valid_policy.created_at, datetime)
    assert isinstance(valid_policy.updated_at, datetime)
    assert valid_policy.priority == 0  # Default
    
    # With priority
    high_priority_policy = Policy(
        policy_id=uuid4(),
        name="High Priority Policy",
        description="Policy with high priority",
        rules={},
        priority=10,
        created_by=owner.agent_id
    )
    test_db.add(high_priority_policy)
    test_db.commit()
    
    assert high_priority_policy.priority == 10
    assert isinstance(high_priority_policy.created_at, datetime)

def test_credential_model(test_db):
    """Test the Credential model validation."""
    # Create required related objects
    agent = Agent(
        agent_id=uuid4(),
        name="Test Agent",
        description="Test agent",
        roles=["user"]
    )
    test_db.add(agent)
    test_db.commit()
    
    owner = Agent(
        agent_id=uuid4(),
        name="Test Owner",
        description="Test owner",
        roles=["owner"]
    )
    test_db.add(owner)
    test_db.commit()
    
    tool = Tool(
        tool_id=uuid4(),
        name="Test Tool",
        description="Test tool",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={},
        params={},
        version="1.0.0",
        owner=owner,
        owner_id=owner.agent_id
    )
    test_db.add(tool)
    test_db.commit()
    
    # Valid credential
    credential_id = uuid4()
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    valid_credential = Credential(
        credential_id=credential_id,
        agent_id=agent.agent_id,
        tool_id=tool.tool_id,
        token="test-token",
        expires_at=expires_at,
        scope="read"
    )
    test_db.add(valid_credential)
    test_db.commit()
    
    assert valid_credential.credential_id == credential_id
    assert valid_credential.agent_id == agent.agent_id
    assert valid_credential.tool_id == tool.tool_id
    assert valid_credential.token == "test-token"
    assert valid_credential.expires_at == expires_at
    assert valid_credential.scope == "read"
    assert isinstance(valid_credential.created_at, datetime)
    assert valid_credential.is_active == True

def test_access_log_model(test_db):
    """Test the AccessLog model validation."""
    # Create required related objects
    agent = Agent(
        agent_id=uuid4(),
        name="Test Agent",
        description="Test agent",
        roles=["user"]
    )
    test_db.add(agent)
    test_db.commit()
    
    owner = Agent(
        agent_id=uuid4(),
        name="Test Owner",
        description="Test owner",
        roles=["owner"]
    )
    test_db.add(owner)
    test_db.commit()
    
    tool = Tool(
        tool_id=uuid4(),
        name="Test Tool",
        description="Test tool",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={},
        params={},
        version="1.0.0",
        owner=owner,
        owner_id=owner.agent_id
    )
    test_db.add(tool)
    test_db.commit()
    
    policy = Policy(
        policy_id=uuid4(),
        name="Test Policy",
        description="Test policy",
        rules={},
        created_by=owner.agent_id
    )
    
    # Add the tool to the policy
    policy.tools.append(tool)
    
    test_db.add(policy)
    test_db.commit()
    
    credential = Credential(
        credential_id=uuid4(),
        agent_id=agent.agent_id,
        tool_id=tool.tool_id,
        token="test-token",
        scope="read",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    test_db.add(credential)
    test_db.commit()

    # Valid access log
    log_id = uuid4()
    valid_log = AccessLog(
        log_id=log_id,
        agent_id=agent.agent_id,
        tool_id=tool.tool_id,
        policy_id=policy.policy_id,
        credential_id=credential.credential_id,
        access_granted=True,
        reason="Access granted",
        request_data={"ip": "127.0.0.1"}
    )
    test_db.add(valid_log)
    test_db.commit()

    assert valid_log.log_id == log_id
    assert valid_log.agent_id == agent.agent_id
    assert valid_log.tool_id == tool.tool_id
    assert valid_log.policy_id == policy.policy_id
    assert valid_log.credential_id == credential.credential_id
    assert valid_log.access_granted is True
    assert valid_log.reason == "Access granted"
    assert valid_log.request_data == {"ip": "127.0.0.1"}
    assert isinstance(valid_log.created_at, datetime)

    # Note: SQLAlchemy models don't validate at initialization like Pydantic 