import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from fastapi import HTTPException
from jose import jwt
import os
from unittest.mock import patch, MagicMock

from tool_registry.auth import (
    verify_password, 
    get_password_hash,
    create_access_token, 
    get_current_agent_token as get_current_agent, 
    authenticate_agent, 
    register_agent,
    agents_db,
    SECRET_KEY,
    ALGORITHM
)
from tool_registry.models import Agent

# Mock dependency for FastAPI's Depends
class MockDependsClass:
    def __init__(self, token):
        self.token = token

@pytest.fixture
def clear_agents_db():
    # Clear the agents_db before each test
    agents_db.clear()
    yield
    agents_db.clear()

@pytest.fixture
def test_agent():
    """Create a test agent for tests."""
    return Agent(
        agent_id=uuid4(),
        name="Test Agent",
        description="Test agent for unit tests",
        roles=["tester", "user"]
    )

def test_password_hashing():
    """Test password hashing and verification."""
    password = "test-password"
    hashed = get_password_hash(password)
    
    # Hashes should be different from the original password
    assert hashed != password
    
    # Verification should work
    assert verify_password(password, hashed)
    
    # Wrong password should fail
    assert not verify_password("wrong-password", hashed)

def test_create_access_token():
    """Test creating JWT access tokens."""
    # Create a token with basic data
    data = {"sub": "test-agent", "role": "user"}
    token = create_access_token(data)
    
    # Token should be a string
    assert isinstance(token, str)
    
    # Decode and verify the token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Check payload
    assert payload["sub"] == "test-agent"
    assert payload["role"] == "user"
    assert "exp" in payload  # Should have an expiration
    
    # Test with custom expiration
    token = create_access_token(data, expires_delta=timedelta(minutes=5))
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Expiration should be about 5 minutes from now
    exp_time = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert (exp_time - now).total_seconds() < 5 * 60 + 5  # Adding 5 seconds for test execution

@pytest.mark.asyncio
async def test_authenticate_agent(clear_agents_db, test_agent):
    """Test agent authentication."""
    # Add a test agent to the database
    agent_id = str(test_agent.agent_id)
    agents_db[agent_id] = test_agent
    
    # Test the special case for "admin"
    agent = await authenticate_agent("admin", "admin_password")
    assert agent is not None
    assert "admin" in agent.roles
    
    # Test the special case for "user"
    agent = await authenticate_agent("user", "user_password")
    assert agent is not None
    assert "user" in agent.roles
    
    # Test with an agent that exists in the database but has no stored password
    agent = await authenticate_agent(agent_id, "any_password")
    assert agent is not None
    assert agent.agent_id == test_agent.agent_id
    
    # Test with non-existent agent
    agent = await authenticate_agent("non-existent", "password")
    assert agent is None

@pytest.mark.asyncio
async def test_register_agent(clear_agents_db):
    """Test registering an agent."""
    # Create an agent to register
    agent = Agent(
        agent_id=uuid4(),
        name="New Agent",
        description="A new agent for testing",
        roles=["user"]
    )
    
    # Register with a password
    password = "test-password"
    registered_agent = register_agent(agent, password)
    
    # Agent should be in database
    agent_id = str(agent.agent_id)
    assert agent_id in agents_db
    assert agents_db[agent_id].name == "New Agent"
    
    # Verify the agent was returned correctly
    assert registered_agent.agent_id == agent.agent_id
    assert registered_agent.name == "New Agent"
    assert registered_agent.roles == ["user"]

@pytest.mark.asyncio
async def test_get_current_agent(clear_agents_db, test_agent):
    """Test getting the current agent from a token."""
    # Add agent to database
    agent_id = str(test_agent.agent_id)
    agents_db[agent_id] = test_agent
    
    # Create admin agent for test
    admin_agent = Agent(
        agent_id=UUID("00000000-0000-0000-0000-000000000001"),
        name="Admin Agent",
        description="Admin agent for testing",
        roles=["admin", "tool_publisher", "policy_admin"]
    )
    agents_db[str(admin_agent.agent_id)] = admin_agent
    
    # Create user agent for test
    user_agent = Agent(
        agent_id=UUID("00000000-0000-0000-0000-000000000002"),
        name="User Agent",
        description="User agent for testing",
        roles=["user", "tester"]
    )
    agents_db[str(user_agent.agent_id)] = user_agent
    
    # Create a token for this agent
    token = create_access_token({"sub": agent_id})
    
    # Test with test tokens
    admin_token = "test_admin_token"
    user_token = "test_user_token"
    
    # Mock the JWT verification
    with patch('tool_registry.auth.jwt.decode') as mock_decode:
        # Case 1: Valid token for existing agent
        mock_decode.return_value = {"sub": agent_id}
        agent = await get_current_agent(token)
        assert agent.agent_id == test_agent.agent_id
        
        # Case 2: Test admin token
        agent = await get_current_agent(admin_token)
        assert agent is not None
        assert "admin" in agent.roles
        
        # Case 3: Test user token
        agent = await get_current_agent(user_token)
        assert agent is not None
        assert "user" in agent.roles
        
        # Case 4: Token with non-existent agent
        mock_decode.return_value = {"sub": "non-existent"}
        with pytest.raises(Exception):
            await get_current_agent(token)
        
        # Case 5: Invalid token (missing sub)
        mock_decode.return_value = {}
        with pytest.raises(Exception):
            await get_current_agent(token)

def test_environment_variables():
    """Test that environment variables are properly used."""
    # Mock environment variables
    with patch.dict(os.environ, {
        "JWT_SECRET_KEY": "test-secret-key",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60"
    }):
        # Re-import to use new environment variables
        from importlib import reload
        import tool_registry.auth
        reload(tool_registry.auth)
        
        # Check the values
        assert tool_registry.auth.SECRET_KEY == "test-secret-key"
        assert tool_registry.auth.ACCESS_TOKEN_EXPIRE_MINUTES == 60 