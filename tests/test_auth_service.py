import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import secrets

from tool_registry.core.auth import AuthService, AgentAuth, ApiKey
from tool_registry.auth.models import SelfRegisterRequest, ApiKeyRequest


@pytest.fixture
def auth_service():
    """Create an instance of AuthService for testing."""
    # Create a mock database getter
    async def mock_db_getter():
        class MockSession:
            def execute(self, query):
                pass
        yield MockSession()
    
    # Create an instance of AuthService with the mock db getter
    service = AuthService(mock_db_getter)
    
    # Return the service
    return service


@pytest.mark.asyncio
async def test_register_agent(auth_service):
    """Test registering a new agent through self-registration."""
    # Create test registration data
    username = f"test_user_{secrets.token_hex(4)}"
    registration_data = SelfRegisterRequest(
        username=username,
        email="test@example.com",
        password="securepassword",
        name="Test User",
        organization="Test Org"
    )
    
    # Register the agent
    agent = await auth_service.register_agent(registration_data, "securepassword")
    
    # Verify the returned agent
    assert agent is not None
    assert agent.name == "Test User"
    assert "user" in agent.roles
    assert "access_tool:public" in agent.permissions
    
    # Verify username was stored
    assert username in auth_service._username_to_agent
    agent_id = auth_service._username_to_agent[username]
    assert agent_id == agent.agent_id
    
    # Verify agent was stored
    assert agent.agent_id in auth_service._agents
    stored_agent = auth_service._agents[agent.agent_id]
    assert stored_agent.name == "Test User"


@pytest.mark.asyncio
async def test_register_agent_duplicate_username(auth_service):
    """Test registering an agent with a duplicate username."""
    # Create and register first agent
    username = f"duplicate_user_{secrets.token_hex(4)}"
    registration_data = SelfRegisterRequest(
        username=username,
        email="first@example.com",
        password="securepassword",
        name="First User",
        organization="Test Org"
    )
    first_agent = await auth_service.register_agent(registration_data, "securepassword")
    assert first_agent is not None
    
    # Try to register second agent with same username
    duplicate_data = SelfRegisterRequest(
        username=username,
        email="second@example.com",
        password="otherpassword",
        name="Second User",
        organization="Other Org"
    )
    second_agent = await auth_service.register_agent(duplicate_data, "otherpassword")
    
    # Verify second registration failed
    assert second_agent is None


@pytest.mark.asyncio
async def test_create_api_key(auth_service):
    """Test creating a new API key."""
    # Create a test agent
    agent_id = uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"],
        permissions=["access_tool:test"]
    )
    auth_service._agents[agent_id] = agent
    
    # Create API key request
    key_request = ApiKeyRequest(
        name="Test Key",
        description="API key for testing",
        expires_in_days=30,
        permissions=[]  # Use agent permissions
    )
    
    # Create the API key
    api_key = await auth_service.create_api_key(agent_id, key_request)
    
    # Verify the API key
    assert api_key is not None
    assert api_key.name == "Test Key"
    assert api_key.agent_id == agent_id
    assert api_key.description == "API key for testing"
    assert api_key.permissions == ["access_tool:test"]  # Inherited from agent
    assert api_key.api_key.startswith("tr_")
    
    # Verify expiration date
    now = datetime.utcnow()
    expires_delta = api_key.expires_at - now
    assert expires_delta.days >= 29  # Allow for slight timing differences
    assert expires_delta.days <= 30
    
    # Verify the key was stored
    assert api_key.key_id in auth_service._api_keys
    stored_key = auth_service._api_keys[api_key.key_id]
    assert stored_key.api_key == api_key.api_key


@pytest.mark.asyncio
async def test_create_api_key_custom_permissions(auth_service):
    """Test creating an API key with custom permissions."""
    # Create a test agent
    agent_id = uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"],
        permissions=["access_tool:test", "admin:read"]
    )
    auth_service._agents[agent_id] = agent
    
    # Create API key request with custom permissions
    key_request = ApiKeyRequest(
        name="Custom Permissions Key",
        description="API key with custom permissions",
        expires_in_days=90,
        permissions=["access_tool:specific"]
    )
    
    # Create the API key
    api_key = await auth_service.create_api_key(agent_id, key_request)
    
    # Verify custom permissions were used
    assert api_key is not None
    assert api_key.permissions == ["access_tool:specific"]
    assert api_key.permissions != agent.permissions


@pytest.mark.asyncio
async def test_create_api_key_no_expiration(auth_service):
    """Test creating an API key without expiration."""
    # Create a test agent
    agent_id = uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"],
        permissions=["access_tool:test"]
    )
    auth_service._agents[agent_id] = agent
    
    # Create API key request without expiration
    key_request = ApiKeyRequest(
        name="Non-expiring Key",
        description="API key without expiration",
        expires_in_days=None,
        permissions=[]
    )
    
    # Create the API key
    api_key = await auth_service.create_api_key(agent_id, key_request)
    
    # Verify no expiration date
    assert api_key is not None
    assert api_key.expires_at is None


@pytest.mark.asyncio
async def test_create_api_key_invalid_agent(auth_service):
    """Test creating an API key for an invalid agent."""
    # Use a random agent_id that doesn't exist
    invalid_agent_id = uuid4()
    
    # Create API key request
    key_request = ApiKeyRequest(
        name="Invalid Agent Key",
        description="This should fail",
        expires_in_days=30
    )
    
    # Try to create the API key
    api_key = await auth_service.create_api_key(invalid_agent_id, key_request)
    
    # Verify creation failed
    assert api_key is None


@pytest.mark.asyncio
async def test_authenticate_with_api_key(auth_service):
    """Test authenticating with a valid API key."""
    # Create a test agent
    agent_id = uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"],
        permissions=["access_tool:test"]
    )
    auth_service._agents[agent_id] = agent
    
    # Create an API key
    key_id = uuid4()
    api_key_str = "tr_testkey123456"
    key = ApiKey(
        key_id=key_id,
        api_key=api_key_str,
        agent_id=agent_id,
        name="Test Key",
        description="For testing",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    auth_service._api_keys[key_id] = key
    
    # Authenticate with the API key
    authenticated_agent = await auth_service.authenticate_with_api_key(api_key_str)
    
    # Verify the returned agent
    assert authenticated_agent is not None
    assert authenticated_agent.agent_id == agent_id
    assert authenticated_agent.name == "Test Agent"
    assert authenticated_agent.roles == ["user"]
    assert authenticated_agent.permissions == ["access_tool:test"]


@pytest.mark.asyncio
async def test_authenticate_with_invalid_api_key(auth_service):
    """Test authenticating with an invalid API key."""
    # Try to authenticate with a non-existent key
    authenticated_agent = await auth_service.authenticate_with_api_key("tr_nonexistentkey")
    
    # Verify authentication failed
    assert authenticated_agent is None


@pytest.mark.asyncio
async def test_authenticate_with_expired_api_key(auth_service):
    """Test authenticating with an expired API key."""
    # Create a test agent
    agent_id = uuid4()
    agent = AgentAuth(
        agent_id=agent_id,
        name="Test Agent",
        roles=["user"],
        permissions=["access_tool:test"]
    )
    auth_service._agents[agent_id] = agent
    
    # Create an expired API key
    key_id = uuid4()
    api_key_str = "tr_expiredkey123"
    key = ApiKey(
        key_id=key_id,
        api_key=api_key_str,
        agent_id=agent_id,
        name="Expired Key",
        description="Expired key for testing",
        created_at=datetime.utcnow() - timedelta(days=60),
        expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
    )
    auth_service._api_keys[key_id] = key
    
    # Try to authenticate with the expired key
    authenticated_agent = await auth_service.authenticate_with_api_key(api_key_str)
    
    # Verify authentication failed
    assert authenticated_agent is None 