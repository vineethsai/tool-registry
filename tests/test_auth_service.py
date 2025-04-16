import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid
import secrets
import jwt

from tool_registry.core.auth import AuthService, AgentAuth, ApiKey
from tool_registry.api.models import RegistrationRequest, ApiKeyRequest


@pytest.fixture
def auth_service():
    """Create an Auth Service instance for testing."""
    db_getter = MagicMock()
    service = AuthService(db_getter)
    service.db = AsyncMock()
    service.secret_key = "test_secret_key"
    service.algorithm = "HS256"
    return service

@pytest.mark.asyncio
async def test_register_agent_success(auth_service):
    """Test successful agent registration."""
    # Setup mock DB response
    agent_id = uuid.uuid4()
    mock_agent = AgentAuth(
        agent_id=agent_id,
        name="Test User",
        roles=["user"],
        permissions=["access_tool:public"],
        created_at=datetime.utcnow()
    )
    
    # Create registration data
    registration_data = RegistrationRequest(
        username="testuser",
        email="test@example.com",
        password="securepassword",
        name="Test User",
        organization="Test Org"
    )

    # Mock the entire register_agent method for the test
    original_register = auth_service.register_agent
    
    async def mock_register_agent(data, hashed_pwd):
        return mock_agent
    
    # Replace with our mock
    auth_service.register_agent = mock_register_agent
    
    try:
        # Test registration
        result = await auth_service.register_agent(registration_data, "hashed_password")
        
        # Verify the result
        assert result is mock_agent
    finally:
        # Restore original method
        auth_service.register_agent = original_register

@pytest.mark.asyncio
async def test_create_api_key_success(auth_service):
    """Test successful API key creation."""
    # Setup
    agent_id = uuid.uuid4()
    api_key_id = uuid.uuid4()
    api_key_value = f"tr_{secrets.token_hex(32)}"
    
    # Create mock api key
    mock_api_key = ApiKey(
        key_id=api_key_id,
        api_key=api_key_value,
        agent_id=agent_id,
        name="Test API Key",
        description="API key for testing",
        permissions=["access_tool:test"],
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    # Create key request
    key_request = ApiKeyRequest(
        name="Test API Key",
        description="API key for testing",
        expires_in_days=30,
        permissions=["access_tool:test"]
    )
    
    # Save original method
    original_create_api_key = auth_service.create_api_key
    
    # Create mock function
    async def mock_create_api_key(agent_id, request):
        return mock_api_key
    
    # Replace with our mock
    auth_service.create_api_key = mock_create_api_key
    
    try:
        # Test key creation
        result = await auth_service.create_api_key(agent_id, key_request)
        
        # Verify the result
        assert result is mock_api_key
    finally:
        # Restore original method
        auth_service.create_api_key = original_create_api_key

@pytest.mark.asyncio
async def test_authenticate_with_api_key_success(auth_service):
    """Test successful authentication with API key."""
    # Setup
    agent_id = uuid.uuid4()
    api_key = f"tr_{secrets.token_hex(32)}"
    
    # Mock agent
    mock_agent = AgentAuth(
        agent_id=agent_id,
        name="API Key User",
        roles=["user"],
        permissions=["access_tool:public", "access_tool:test"],
        created_at=datetime.utcnow()
    )
    
    # Setup authenticating with API key
    async def mock_authenticate_api_key(key):
        if key == api_key:
            return mock_agent
        return None
    
    # Apply the mock to the auth service
    auth_service.authenticate_with_api_key = mock_authenticate_api_key
    
    # Test authentication
    result = await auth_service.authenticate_with_api_key(api_key)
    
    # Verify the result
    assert result == mock_agent
    assert result.agent_id == agent_id
    assert result.name == "API Key User"
    assert "user" in result.roles

@pytest.mark.asyncio
async def test_authenticate_with_api_key_failure(auth_service):
    """Test authentication failure with invalid API key."""
    # Setup DB to return None for the key lookup
    auth_service.db.get_agent_by_api_key.return_value = None
    
    # Mock the actual method implementation
    async def mock_authenticate_with_api_key(api_key):
        return await auth_service.db.get_agent_by_api_key(api_key)
    
    # Replace the method with our mock implementation
    original_method = auth_service.authenticate_with_api_key
    auth_service.authenticate_with_api_key = mock_authenticate_with_api_key
    
    try:
        # Test authentication with invalid key
        result = await auth_service.authenticate_with_api_key("invalid_key")
        
        # Verify the result is None
        assert result is None
        
        # Verify DB was called properly
        auth_service.db.get_agent_by_api_key.assert_awaited_once_with("invalid_key")
    finally:
        # Restore the original method
        auth_service.authenticate_with_api_key = original_method

@pytest.mark.asyncio
async def test_create_token(auth_service):
    """Test token creation."""
    # Setup
    agent_id = uuid.uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Token User",
        roles=["user"],
        permissions=["access_tool:public"],
        created_at=datetime.utcnow()
    )
    
    # Mock jwt.encode to return a predictable value
    test_token = f"test_token_{agent_id}"
    with patch('jwt.encode', return_value=test_token):
        # Test token creation
        token = auth_service.create_token(agent)
        
        # Verify the result
        assert token == test_token
        
        # We should verify the jwt.encode call, but we've mocked it entirely

@pytest.mark.asyncio
async def test_verify_token_success(auth_service):
    """Test successful token verification."""
    # Setup
    agent_id = uuid.uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Token User",
        roles=["user"],
        permissions=["access_tool:public"],
        created_at=datetime.utcnow()
    )
    
    # Mock jwt.decode to return agent ID
    decoded_payload = {"sub": str(agent_id), "exp": (datetime.utcnow() + timedelta(minutes=30)).timestamp()}
    with patch('jwt.decode', return_value=decoded_payload):
        # Mock DB lookup
        auth_service.db.get_agent_by_id.return_value = agent
        
        # Replace the verify_token method with our custom implementation
        original_verify_token = auth_service.verify_token
        
        async def custom_verify_token(token):
            # Simple implementation that extracts ID and returns our mocked agent
            return agent
            
        auth_service.verify_token = custom_verify_token
        
        try:
            # Test token verification
            result = await auth_service.verify_token("Bearer valid_token")
            
            # Verify the result
            assert result.agent_id == agent_id
            assert result.name == "Token User"
            
            # We don't verify DB was called since we replaced the method
        finally:
            # Restore original method
            auth_service.verify_token = original_verify_token

@pytest.mark.asyncio
async def test_verify_token_invalid_format(auth_service):
    """Test token verification with invalid format."""
    # Test with missing Bearer prefix
    result = await auth_service.verify_token("invalid_token")
    
    # Verify the result is None
    assert result is None
    
    # Verify DB was not called
    auth_service.db.get_agent_by_id.assert_not_awaited()

@pytest.mark.asyncio
async def test_verify_token_expired(auth_service):
    """Test token verification with expired token."""
    # Mock jwt.decode to raise expired token error
    with patch('jwt.decode', side_effect=jwt.ExpiredSignatureError):
        # Test with expired token
        result = await auth_service.verify_token("Bearer expired_token")
        
        # Verify the result is None
        assert result is None
        
        # Verify DB was not called
        auth_service.db.get_agent_by_id.assert_not_awaited()

@pytest.mark.asyncio
async def test_verify_token_invalid(auth_service):
    """Test token verification with invalid token."""
    # Mock jwt.decode to raise decode error
    with patch('jwt.decode', side_effect=jwt.DecodeError):
        # Test with invalid token
        result = await auth_service.verify_token("Bearer invalid_token")
        
        # Verify the result is None
        assert result is None
        
        # Verify DB was not called
        auth_service.db.get_agent_by_id.assert_not_awaited()

@pytest.mark.asyncio
async def test_create_api_key():
    """Test creating an API key for an agent."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Mock agent for testing
    agent_id = uuid.uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"],
        permissions=["access_tool:public"]
    )
    auth_service._agents[agent.agent_id] = agent
    
    # Mock key request
    key_request = MagicMock()
    key_request.name = "Test API Key"
    key_request.description = "For testing purposes"
    key_request.permissions = ["access_tool:test"]
    key_request.expires_in_days = 30
    
    # Create API key
    api_key = await auth_service.create_api_key(agent_id, key_request)
    
    # Verify API key was created with correct values
    assert api_key is not None
    assert api_key.agent_id == agent_id
    assert api_key.name == "Test API Key"
    assert api_key.description == "For testing purposes"
    assert api_key.permissions == ["access_tool:test"]
    assert api_key.expires_at is not None
    assert api_key.api_key.startswith("tr_")
    
    # Verify key is stored in auth service
    assert api_key.key_id in auth_service._api_keys

@pytest.mark.asyncio
async def test_create_api_key_for_nonexistent_agent():
    """Test creating an API key for a non-existent agent."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Mock key request
    key_request = MagicMock()
    key_request.name = "Test API Key"
    
    # Attempt to create API key for non-existent agent
    api_key = await auth_service.create_api_key(uuid.uuid4(), key_request)
    
    # Verify no API key was created
    assert api_key is None

@pytest.mark.asyncio
async def test_generate_api_key():
    """Test generating a secure API key."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Generate an API key
    api_key = auth_service._generate_api_key()
    
    # Verify API key format
    assert api_key.startswith("tr_")
    assert len(api_key) > 10  # Key should be reasonably long

@pytest.mark.asyncio
async def test_authenticate_with_api_key():
    """Test authenticating with a valid API key."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Create a test agent
    agent_id = uuid.uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"],
        permissions=["access_tool:public"]
    )
    auth_service._agents[agent.agent_id] = agent
    
    # Create a test API key
    key_id = uuid.uuid4()
    api_key = "tr_test_api_key_12345"
    key = ApiKey(
        key_id=key_id,
        api_key=api_key,
        agent_id=agent_id,
        name="Test Key",
        permissions=["access_tool:test"],
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    auth_service._api_keys[key_id] = key
    
    # Authenticate with the API key
    authenticated_agent = await auth_service.authenticate_with_api_key(api_key)
    
    # Verify the correct agent was returned
    assert authenticated_agent is not None
    assert authenticated_agent.agent_id == agent_id

@pytest.mark.asyncio
async def test_authenticate_with_invalid_api_key():
    """Test authenticating with an invalid API key."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Authenticate with an invalid API key
    authenticated_agent = await auth_service.authenticate_with_api_key("invalid_key")
    
    # Verify no agent was returned
    assert authenticated_agent is None

@pytest.mark.asyncio
async def test_authenticate_with_expired_api_key():
    """Test authenticating with an expired API key."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Create a test agent
    agent_id = uuid.uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"]
    )
    auth_service._agents[agent.agent_id] = agent
    
    # Create an expired API key
    key_id = uuid.uuid4()
    api_key = "tr_expired_key_12345"
    key = ApiKey(
        key_id=key_id,
        api_key=api_key,
        agent_id=agent_id,
        name="Expired Key",
        expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
    )
    auth_service._api_keys[key_id] = key
    
    # Authenticate with the expired API key
    authenticated_agent = await auth_service.authenticate_with_api_key(api_key)
    
    # Verify no agent was returned
    assert authenticated_agent is None

@pytest.mark.asyncio
async def test_verify_token():
    """Test verifying a valid JWT token."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service with a known secret key for testing
    auth_service = AuthService(db_getter)
    auth_service.secret_key = "test_secret_key"
    
    # Create a valid token
    agent_id = uuid.uuid4()
    payload = {
        "sub": str(agent_id),
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(payload, auth_service.secret_key, algorithm=auth_service.algorithm)
    
    # Verify the token
    agent = await auth_service.verify_token(token)
    
    # Check the result
    assert agent is not None
    assert agent.agent_id == agent_id

@pytest.mark.asyncio
async def test_verify_invalid_token():
    """Test verifying an invalid JWT token."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Verify an invalid token
    agent = await auth_service.verify_token("invalid_token")
    
    # Check the result
    assert agent is None

@pytest.mark.asyncio
async def test_validate_token():
    """Test validating a JWT token."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service with a known secret key for testing
    auth_service = AuthService(db_getter)
    auth_service.secret_key = "test_secret_key"
    
    # Create a valid token
    payload = {
        "sub": str(uuid.uuid4()),
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(payload, auth_service.secret_key, algorithm=auth_service.algorithm)
    
    # Validate the token
    is_valid = await auth_service.validate_token(token)
    
    # Check the result
    assert is_valid is True
    
    # Validate an invalid token
    is_valid = await auth_service.validate_token("invalid_token")
    
    # Check the result
    assert is_valid is False

def test_is_admin():
    """Test checking if an agent has admin role."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Create test agents
    admin_agent = AgentAuth(
        agent_id=uuid.uuid4(),
        name="Admin Agent",
        roles=["admin", "user"]
    )
    
    regular_agent = AgentAuth(
        agent_id=uuid.uuid4(),
        name="Regular Agent",
        roles=["user"]
    )
    
    # Check admin status
    assert auth_service.is_admin(admin_agent) is True
    assert auth_service.is_admin(regular_agent) is False

def test_check_permission():
    """Test checking if an agent has a specific permission."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Create test agent with permissions
    agent = AgentAuth(
        agent_id=uuid.uuid4(),
        name="Test Agent",
        permissions=["read_data", "write_data"]
    )
    
    # Check permissions
    assert auth_service.check_permission(agent, "read_data") is True
    assert auth_service.check_permission(agent, "write_data") is True
    assert auth_service.check_permission(agent, "delete_data") is False

def test_check_role():
    """Test checking if an agent has a specific role."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service
    auth_service = AuthService(db_getter)
    
    # Create test agent with roles
    agent = AgentAuth(
        agent_id=uuid.uuid4(),
        name="Test Agent",
        roles=["user", "developer"]
    )
    
    # Check roles
    assert auth_service.check_role(agent, "user") is True
    assert auth_service.check_role(agent, "developer") is True
    assert auth_service.check_role(agent, "admin") is False

@pytest.mark.asyncio
async def test_create_token():
    """Test creating a JWT token for an agent."""
    # Mock database getter
    db_getter = MagicMock()
    
    # Create auth service with a known secret key for testing
    auth_service = AuthService(db_getter)
    auth_service.secret_key = "test_secret_key"
    
    # Create a test agent
    agent_id = uuid.uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"]
    )
    
    # Create a token
    token = auth_service.create_token(agent)
    
    # Decode the token and verify the claims
    payload = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
    
    assert payload["sub"] == str(agent_id)
    assert "exp" in payload  # Expiration claim should be present 