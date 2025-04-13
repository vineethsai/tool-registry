import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from tool_registry.api.app import app, oauth2_scheme
from tool_registry.core.auth import AuthService, AgentAuth, ApiKey
from tool_registry.auth.models import SelfRegisterRequest, ApiKeyRequest


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    """Create a mock of the auth service with methods for our tests."""
    # Create a mock AuthService
    auth_service = MagicMock(spec=AuthService)
    
    # Add required attributes for JWT encoding
    auth_service.secret_key = "test_secret_key"
    auth_service.algorithm = "HS256"
    
    # Setup base behavior for register_agent method
    async def mock_register_agent(registration_data, password):
        # Reject registration for specific test username
        if registration_data.username == "existing_user":
            return None
            
        # Otherwise return a mocked agent
        return AgentAuth(
            agent_id=uuid4(),
            name=registration_data.name,
            roles=["user"],
            permissions=["access_tool:public"],
            created_at=datetime.utcnow()
        )
    auth_service.register_agent.side_effect = mock_register_agent
    
    # Setup behavior for create_api_key method
    async def mock_create_api_key(agent_id, key_request):
        # Test for invalid agent ID
        if agent_id == UUID("00000000-0000-0000-0000-000000000000"):
            return None
            
        # Calculate expiration if provided
        expires_at = None
        if key_request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=key_request.expires_in_days)
            
        # Return a mock API key
        return ApiKey(
            key_id=uuid4(),
            api_key=f"tr_test_api_key_{agent_id}",
            agent_id=agent_id,
            name=key_request.name,
            description=key_request.description,
            permissions=key_request.permissions or [],
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )
    auth_service.create_api_key.side_effect = mock_create_api_key
    
    # Setup behavior for authenticate_with_api_key method
    async def mock_authenticate_with_api_key(api_key):
        # Return None for invalid key
        if api_key == "invalid_key":
            return None
            
        # Return None for expired key
        if api_key == "expired_key":
            return None
            
        # Return mock agent for valid key
        return AgentAuth(
            agent_id=uuid4(),
            name="API Key User",
            roles=["user"],
            permissions=["access_tool:public"],
            created_at=datetime.utcnow()
        )
    auth_service.authenticate_with_api_key.side_effect = mock_authenticate_with_api_key
    
    return auth_service


@pytest.mark.asyncio
async def test_self_registration_success(test_client, mock_auth_service):
    """Test successful self-registration."""
    with patch('tool_registry.api.app.auth_service', mock_auth_service):
        # Create registration data
        registration_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword",
            "name": "New User",
            "organization": "Test Organization"
        }
        
        # Make request to register endpoint
        response = test_client.post("/register", json=registration_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify auth service was called correctly
        mock_auth_service.register_agent.assert_called_once()
        call_args = mock_auth_service.register_agent.call_args[0]
        assert call_args[0].username == "newuser"
        assert call_args[0].email == "newuser@example.com"
        assert call_args[1] == "securepassword"  # password


@pytest.mark.asyncio
async def test_self_registration_duplicate_username(test_client, mock_auth_service):
    """Test self-registration with duplicate username (should fail)."""
    with patch('tool_registry.api.app.auth_service', mock_auth_service):
        # Create registration data with existing username
        registration_data = {
            "username": "existing_user",
            "email": "existing@example.com",
            "password": "securepassword",
            "name": "Existing User",
            "organization": "Test Organization"
        }
        
        # Make request to register endpoint
        response = test_client.post("/register", json=registration_data)
        
        # Verify failure response
        assert response.status_code == 409
        result = response.json()
        assert "detail" in result
        assert "exists" in result["detail"]


@pytest.mark.asyncio
async def test_api_key_generation(test_client, mock_auth_service):
    """Test API key generation endpoint."""
    # Create a direct ApiKeyResponse instead of mocking
    with patch('tool_registry.api.app.auth_service', mock_auth_service):
        # Set up the auth service mock to return a valid API key with proper data types
        key_id = uuid4()
        mock_api_key = MagicMock()
        mock_api_key.key_id = key_id
        mock_api_key.api_key = "tr_testapikey123456789"
        mock_api_key.name = "Test API Key"
        mock_api_key.expires_at = datetime.utcnow() + timedelta(days=30)
        mock_api_key.created_at = datetime.utcnow()
        
        # Make the auth_service.create_api_key method return our mock
        mock_auth_service.create_api_key.return_value = mock_api_key
        
        # Create API key request
        key_request = {
            "name": "Test API Key",
            "description": "Key for testing",
            "expires_in_days": 30,
            "permissions": ["access_tool:test"]
        }
        
        # Make request to create API key - no auth header needed now
        response = test_client.post(
            "/api-keys", 
            json=key_request
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify auth service was called correctly
        mock_auth_service.create_api_key.assert_called_once()
        
        # Verify response contains expected data
        data = response.json()
        assert "key_id" in data
        assert "api_key" in data
        assert "name" in data
        assert data["name"] == "Test API Key"


@pytest.mark.asyncio
async def test_api_key_authentication_success(test_client, mock_auth_service):
    """Test successful authentication with API key."""
    # Create a direct TokenResponse
    with patch('tool_registry.api.app.auth_service', mock_auth_service):
        # Make request to authenticate with API key
        response = test_client.post(
            "/auth/api-key",
            headers={"api-key": "valid_test_key"}
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify we got a token response
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["access_token"] == "test_token"
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_api_key_authentication_invalid_key(test_client, mock_auth_service):
    """Test authentication with invalid API key."""
    with patch('tool_registry.api.app.auth_service', mock_auth_service):
        # Make request with invalid key
        response = test_client.post(
            "/auth/api-key",
            headers={"api-key": "invalid_key"}
        )
        
        # Verify failure response
        assert response.status_code == 401
        result = response.json()
        assert "detail" in result
        assert "Invalid API key" in result["detail"]


@pytest.mark.asyncio
async def test_api_key_authentication_expired_key(test_client, mock_auth_service):
    """Test authentication with expired API key."""
    with patch('tool_registry.api.app.auth_service', mock_auth_service):
        # Make request with expired key
        response = test_client.post(
            "/auth/api-key",
            headers={"api-key": "expired_key"}
        )
        
        # Verify failure response
        assert response.status_code == 401
        result = response.json()
        assert "detail" in result
        assert "Invalid API key" in result["detail"]


@pytest.mark.asyncio
async def test_api_key_generation_failure(test_client, mock_auth_service):
    """Test API key generation failure."""
    with patch('tool_registry.api.app.auth_service', mock_auth_service):
        # Create API key request with a permission that triggers failure
        key_request = {
            "name": "Test API Key",
            "description": "Key for testing",
            "expires_in_days": 30,
            "permissions": ["fail"]  # This will trigger the failure
        }
        
        # Make request to create API key
        response = test_client.post(
            "/api-keys", 
            json=key_request
        )
        
        # Verify failure response
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "Failed to create API key" in result["detail"] 