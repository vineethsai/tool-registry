import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import secrets
import jwt

from tool_registry.api.app import app, auth_service


class TestAuthIntegration:
    """Integration tests for the authentication flow."""
    
    @pytest.fixture
    def client(self):
        """Test client for the FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def setup_auth_service(self):
        """Setup the auth service with needed testing methods."""
        # Store original methods to restore after tests
        original_register = auth_service.register_agent
        original_create_key = auth_service.create_api_key
        original_authenticate = auth_service.authenticate_with_api_key
        original_verify = auth_service.verify_token
        
        # Create an agent ID for our test flow
        test_agent_id = uuid4()
        
        # Replace methods with test versions
        async def mock_register_agent(registration_data, password):
            return AgentAuth(
                agent_id=test_agent_id,
                name=registration_data.name,
                roles=["user"],
                permissions=["access_tool:public"],
                created_at=datetime.utcnow()
            )
        
        async def mock_create_api_key(agent_id, key_request):
            # Only succeed if agent_id matches our test agent
            if agent_id == test_agent_id:
                return ApiKey(
                    key_id=uuid4(),
                    api_key="tr_integration_test_key",
                    agent_id=agent_id,
                    name=key_request.name,
                    description=key_request.description,
                    permissions=key_request.permissions or ["access_tool:public"],
                    created_at=datetime.utcnow(),
                    expires_at=(datetime.utcnow() + timedelta(days=key_request.expires_in_days) 
                               if key_request.expires_in_days else None)
                )
            return None
        
        async def mock_authenticate_with_api_key(api_key):
            if api_key == "tr_integration_test_key":
                return AgentAuth(
                    agent_id=test_agent_id,
                    name="Integration Test User",
                    roles=["user"],
                    permissions=["access_tool:public"],
                    created_at=datetime.utcnow()
                )
            return None
        
        async def mock_verify_token(token):
            # For our integration test, consider the token valid if it matches a specific pattern
            if token == f"Bearer {test_agent_id}":
                return AgentAuth(
                    agent_id=test_agent_id,
                    name="Integration Test User",
                    roles=["user"],
                    permissions=["access_tool:public"],
                    created_at=datetime.utcnow()
                )
            return None
            
        # Apply the mocks
        auth_service.register_agent = mock_register_agent
        auth_service.create_api_key = mock_create_api_key
        auth_service.authenticate_with_api_key = mock_authenticate_with_api_key
        auth_service.verify_token = mock_verify_token
        
        # Patch jwt.encode to return a predictable token
        original_encode = jwt.encode
        jwt.encode = lambda *args, **kwargs: f"{test_agent_id}"
        
        yield test_agent_id
        
        # Restore original methods after test
        auth_service.register_agent = original_register
        auth_service.create_api_key = original_create_key
        auth_service.authenticate_with_api_key = original_authenticate
        auth_service.verify_token = original_verify
        jwt.encode = original_encode
    
    @pytest.mark.asyncio
    async def test_full_auth_flow(self, client, setup_auth_service):
        """Test the entire authentication flow from registration to API key usage."""
        test_agent_id = setup_auth_service
        
        # Step 1: Register a new user
        registration_data = {
            "username": f"flow_test_user_{secrets.token_hex(4)}",
            "email": "flowtest@example.com",
            "password": "secureflowpassword",
            "name": "Flow Test User",
            "organization": "Flow Test Org"
        }
        
        register_response = client.post("/register", json=registration_data)
        assert register_response.status_code == 200
        register_result = register_response.json()
        assert register_result["name"] == "Flow Test User"
        assert "user" in register_result["roles"]
        
        # Step 2: Login with the new user to get a token
        login_response = client.post(
            "/token",
            data={
                "username": registration_data["username"],
                "password": registration_data["password"]
            }
        )
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "access_token" in login_result
        assert login_result["token_type"] == "bearer"
        
        # Get the token for subsequent requests
        token = login_result["access_token"]
        
        # Step 3: Create an API key using the token
        key_request = {
            "name": "Flow Test API Key",
            "description": "API key for flow testing",
            "expires_in_days": 30,
            "permissions": ["access_tool:test_flow"]
        }
        
        create_key_response = client.post(
            "/api-keys",
            json=key_request,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_key_response.status_code == 200
        key_result = create_key_response.json()
        assert key_result["name"] == "Flow Test API Key"
        assert "api_key" in key_result
        
        # Get the API key for the next step
        api_key = key_result["api_key"]
        
        # Step 4: Use the API key to get a token
        api_auth_response = client.post(
            "/auth/api-key",
            headers={"api-key": api_key}
        )
        assert api_auth_response.status_code == 200
        api_auth_result = api_auth_response.json()
        assert "access_token" in api_auth_result
        assert api_auth_result["token_type"] == "bearer"
        
        # Get the API-generated token
        api_token = api_auth_result["access_token"]
        
        # Step 5: Use the API-generated token to access a protected endpoint
        tools_response = client.get(
            "/tools",
            headers={"Authorization": f"Bearer {api_token}"}
        )
        
        # Verify successful access with the API-generated token
        assert tools_response.status_code == 200
        
        # This test has successfully verified the full authentication flow:
        # 1. Self-registration
        # 2. Login with username/password to get token
        # 3. Create API key using token
        # 4. Get a token using the API key
        # 5. Access a protected resource with the API key-generated token


# Import these here to avoid circular imports in the mocks
from tool_registry.core.auth import AgentAuth, ApiKey 