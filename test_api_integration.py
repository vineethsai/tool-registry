import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
import asyncio
from fastapi import HTTPException, status
import json

from tool_registry.main import app
from tool_registry.models import Agent, Tool, Policy, Credential, AccessLog

@pytest.fixture
def mock_auth_and_agents(test_admin_agent, test_user_agent):
    """Patch authentication and agent management."""
    with patch('tool_registry.auth.authenticate_agent') as mock_auth:
        with patch('tool_registry.auth.get_current_agent') as mock_current_agent:
            with patch('tool_registry.main.get_current_agent') as mock_main_current_agent:
                with patch('tool_registry.auth.agents_db') as mock_agents_db:
                    with patch('tool_registry.main.oauth2_scheme') as mock_oauth2_scheme:
                        print(f"\nDEBUG: Mocking auth functions")
                        print(f"DEBUG: test_admin_agent.agent_id = {test_admin_agent.agent_id}")
                        print(f"DEBUG: test_user_agent.agent_id = {test_user_agent.agent_id}")
                        
                        # Setup mock token extraction
                        async def extract_token(request):
                            auth_header = request.headers.get("Authorization", "")
                            print(f"DEBUG: oauth2_scheme called with header: {auth_header}")
                            if auth_header.startswith("Bearer "):
                                token = auth_header.replace("Bearer ", "")
                                return token
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Not authenticated",
                                headers={"WWW-Authenticate": "Bearer"},
                            )
                            
                        mock_oauth2_scheme.side_effect = extract_token
                        
                        # Setup mock authentication
                        async def async_auth(username, password):
                            print(f"DEBUG: authenticate_agent called with {username}, {password}")
                            if username == "admin" and password == "admin_password":
                                return test_admin_agent
                            elif username == "user" and password == "user_password":
                                return test_user_agent
                            return None
                        
                        mock_auth.side_effect = async_auth
                        
                        # Setup mock agent database
                        mock_agents_db.__getitem__.side_effect = lambda key: (
                            test_admin_agent if key == str(test_admin_agent.agent_id) else
                            test_user_agent if key == str(test_user_agent.agent_id) else
                            None
                        )
                        
                        mock_agents_db.get.side_effect = lambda key, default=None: (
                            test_admin_agent if key == str(test_admin_agent.agent_id) else
                            test_user_agent if key == str(test_user_agent.agent_id) else
                            default
                        )
                        
                        # Setup current agent (for auth.py)
                        async def get_agent_from_token(token):
                            print(f"DEBUG: get_agent_from_token called with {token}")
                            if token == "test_admin_token":
                                return test_admin_agent
                            elif token == "test_user_token":
                                return test_user_agent
                            else:
                                print(f"DEBUG: Invalid token: {token}")
                                raise HTTPException(
                                    status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Could not validate credentials",
                                    headers={"WWW-Authenticate": "Bearer"},
                                )
                        
                        # Mock the dependency in auth.py
                        mock_current_agent.side_effect = get_agent_from_token
                        
                        # Mock the dependency in main.py directly (this is the key fix)
                        mock_main_current_agent.side_effect = get_agent_from_token
                        
                        yield 

@pytest.fixture
def client():
    """Create a test client for the app."""
    from fastapi.testclient import TestClient
    from tool_registry.main import app
    
    test_client = TestClient(app)
    test_client.headers = {"Authorization": "Bearer test-token"}
    return test_client

def test_tool_access_endpoint(client, test_user_token, test_user_agent, test_tool, mock_authorization_service, mock_credential_vendor):
    """Test that the tool access endpoint returns a credential for an authorized request."""
    import json
    import asyncio
    import unittest.mock
    
    # Create a future for the tool to return
    future_tool = asyncio.Future()
    future_tool.set_result(test_tool)
    
    # Create the test credential
    credential = Credential(
        credential_id=UUID("00000000-0000-0000-0000-000000000005"),
        agent_id=test_user_agent.agent_id,
        tool_id=test_tool.tool_id,
        token="test-credential-token",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        scope=["read", "write"]
    )
    
    # Setup a temporary app module with our mocks
    with unittest.mock.patch("tool_registry.api.app.tool_registry.get_tool", return_value=future_tool):
        with unittest.mock.patch("tool_registry.api.app.auth_service.check_permission", return_value=True):
            with unittest.mock.patch("tool_registry.api.app.get_current_agent", return_value=test_user_agent):
                with unittest.mock.patch("tool_registry.api.app.credential_vendor.generate_credential", return_value=credential):
                    # Make the request
                    response = client.post(
                        f"/tools/{test_tool.tool_id}/access",
                        headers={"Authorization": f"Bearer {test_user_token}"},
                        json={"scopes": ["read", "write"]}
                    )
                    
                    # Print debug info
                    print(f"Response status: {response.status_code}")
                    print(f"Response content: {response.content.decode()}")
                    
                    # Assert response
                    assert response.status_code == 200
                    response_data = json.loads(response.content)
                    assert "credential" in response_data
                    assert "credential_id" in response_data["credential"]
                    assert response_data["tool"]["tool_id"] == str(test_tool.tool_id)

def test_token_endpoint_simple(client):
    """A simplified test of the token endpoint."""
    from unittest.mock import patch
    import jwt
    from datetime import datetime, timedelta
    
    # Test a login
    response = client.post(
        "/token",
        data={"username": "admin", "password": "admin_password"}
    )
    
    # Verify the results
    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    assert isinstance(result["access_token"], str)
    assert len(result["access_token"]) > 10  # Just check it's a reasonable length

def test_token_endpoint(client, mock_auth_and_agents):
    """Test the token endpoint for authentication."""
    # Test valid admin login
    response = client.post(
        "/token",
        data={"username": "admin", "password": "admin_password"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    
    # Test valid user login
    response = client.post(
        "/token",
        data={"username": "user", "password": "user_password"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    
    # Test invalid login
    response = client.post(
        "/token",
        data={"username": "invalid", "password": "invalid"}
    )
    
    assert response.status_code == 401

def test_my_simple_test():
    """A simple test to verify our test structure."""
    assert True

def test_sample():
    """Just a simple test to verify our test structure."""
    assert True 

def test_tool_access_endpoint2(client):
    """Test that the tool access endpoint returns a credential for an authorized request."""
    import json
    import asyncio
    from unittest.mock import patch, MagicMock
    from tool_registry.models import Credential, Tool, Agent
    from uuid import UUID
    from datetime import datetime, timedelta
    
    # Create test objects
    test_user_agent = Agent(
        agent_id=UUID("00000000-0000-0000-0000-000000000002"),
        name="User Agent",
        description="User agent for testing",
        roles=["user", "tester"]
    )
    
    test_tool = Tool(
        tool_id=UUID("00000000-0000-0000-0000-000000000003"),
        name="Test Tool",
        description="Test tool for integration testing",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={"header_name": "X-API-Key"},
        params={"text": {"type": "string", "required": True}},
        version="1.0.0",
        owner="admin",
        tags=["test", "integration"],
        allowed_scopes=["read", "write", "execute"]
    )
    
    # Create a future for the tool
    future_tool = asyncio.Future()
    future_tool.set_result(test_tool)
    
    # Create a credential for the response
    credential = Credential(
        credential_id=UUID("00000000-0000-0000-0000-000000000005"),
        agent_id=test_user_agent.agent_id,
        tool_id=test_tool.tool_id,
        token="test-credential-token",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        scope=["read", "write"]
    )
    
    # Create a future for the credential
    future_credential = asyncio.Future()
    future_credential.set_result(credential)
    
    # Create mocks for the OAuth2 scheme
    async def mock_oauth2_scheme(request):
        return "test-token"
    
    # Create a patch context
    with patch('tool_registry.api.app.oauth2_scheme', side_effect=mock_oauth2_scheme):
        with patch('tool_registry.auth.oauth2_scheme', side_effect=mock_oauth2_scheme):
            with patch('tool_registry.api.app.get_current_agent', return_value=test_user_agent):
                with patch('tool_registry.auth.get_current_agent', return_value=test_user_agent):
                    with patch('tool_registry.api.app.tool_registry.get_tool', return_value=future_tool):
                        with patch('tool_registry.api.app.credential_vendor.generate_credential', return_value=future_credential):
                            with patch('tool_registry.api.app.auth_service.check_permission', return_value=True):
                                
                                # Make the request
                                headers = {"Authorization": "Bearer test-token"}
                                response = client.post(
                                    f"/tools/{test_tool.tool_id}/access",
                                    headers=headers,
                                    json={"scopes": ["read", "write"]}
                                )
                                
                                # Debug information
                                print(f"Response status: {response.status_code}")
                                if response.status_code != 200:
                                    print(f"Response content: {response.content.decode()}")
                                
                                # Assertion
                                assert response.status_code == 200 

def test_health_check_simple(client):
    """Simple test for the health check endpoint that doesn't require authentication."""
    response = client.get("/health")
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "healthy" 

def test_tool_access_endpoint_simple():
    """Test the tool access endpoint with a minimal approach."""
    from fastapi.testclient import TestClient
    from tool_registry.main import app
    import unittest.mock
    from unittest.mock import patch, MagicMock
    import json
    import asyncio
    
    # Create our own test client
    client = TestClient(app)
    
    # Create a mock response for the tool registry get_tool call
    mock_tool_future = asyncio.Future()
    mock_tool = MagicMock()
    mock_tool.tool_id = "00000000-0000-0000-0000-000000000003"
    mock_tool_future.set_result(mock_tool)
    
    # Create a mock agent
    mock_agent = MagicMock()
    mock_agent.agent_id = "00000000-0000-0000-0000-000000000002"
    
    # Create a mock credential
    mock_credential = MagicMock()
    mock_credential.credential_id = "00000000-0000-0000-0000-000000000005"
    mock_credential.token = "test-credential-token"
    
    # Apply mock patches for the essential parts
    with patch('tool_registry.auth.get_current_agent', return_value=mock_agent):
        with patch('tool_registry.api.app.get_current_agent', return_value=mock_agent):
            with patch('tool_registry.api.app.tool_registry.get_tool', return_value=mock_tool_future):
                with patch('tool_registry.api.app.auth_service.check_permission', return_value=True):
                    with patch('tool_registry.api.app.credential_vendor.generate_credential', return_value=mock_credential):
                        
                        # Make the request with a test token
                        response = client.post(
                            f"/tools/{mock_tool.tool_id}/access", 
                            headers={"Authorization": "Bearer test-token"},
                            json={"scopes": ["read", "write"]}
                        )
                        
                        # Print for debugging
                        print(f"Response: {response.status_code}")
                        print(f"Response body: {response.text}")
                        
                        # Assert expectations
                        assert response.status_code == 200 

def test_tool_access_endpoint_final():
    """Test the tool access endpoint with comprehensive mocking approach."""
    from fastapi.testclient import TestClient
    from tool_registry.main import app
    import unittest.mock
    from unittest.mock import patch, MagicMock
    import json
    import asyncio
    from uuid import UUID
    
    # Create our own test client
    client = TestClient(app)
    
    # Create a mock response for the tool registry get_tool call
    mock_tool_future = asyncio.Future()
    mock_tool = MagicMock()
    mock_tool.tool_id = UUID("00000000-0000-0000-0000-000000000003")
    mock_tool_future.set_result(mock_tool)
    
    # Create a mock agent
    mock_agent = MagicMock()
    mock_agent.agent_id = UUID("00000000-0000-0000-0000-000000000002")
    
    # Create a mock credential
    mock_credential = MagicMock()
    mock_credential.credential_id = UUID("00000000-0000-0000-0000-000000000005")
    mock_credential.token = "test-credential-token"
    
    # Create a future for the credential
    mock_credential_future = asyncio.Future()
    mock_credential_future.set_result(mock_credential)
    
    # Need to bypass the OAuth2 scheme
    async def mock_oauth2(request):
        return "test-token"
    
    # Need to bypass JWT verification
    def mock_jwt_decode(token, key, algorithms, **kwargs):
        return {"sub": "00000000-0000-0000-0000-000000000002"}
    
    # Apply all patches
    with patch('tool_registry.auth.oauth2_scheme', side_effect=mock_oauth2):
        with patch('tool_registry.api.app.oauth2_scheme', side_effect=mock_oauth2): 
            with patch('tool_registry.auth.jwt.decode', side_effect=mock_jwt_decode):
                with patch('tool_registry.api.app.get_current_agent', return_value=mock_agent):
                    with patch('tool_registry.auth.get_current_agent', return_value=mock_agent):
                        with patch('tool_registry.api.app.tool_registry.get_tool', return_value=mock_tool_future):
                            with patch('tool_registry.api.app.auth_service.check_permission', return_value=True):
                                with patch('tool_registry.api.app.credential_vendor.generate_credential', return_value=mock_credential_future):
                                    
                                    # Make the request with a test token
                                    response = client.post(
                                        f"/tools/{mock_tool.tool_id}/access", 
                                        headers={"Authorization": "Bearer test-token"},
                                        json={"scopes": ["read", "write"]}
                                    )
                                    
                                    # Print for debugging
                                    print(f"Response: {response.status_code}")
                                    print(f"Response body: {response.text}")
                                    
                                    # Assert expectations
                                    assert response.status_code == 200 