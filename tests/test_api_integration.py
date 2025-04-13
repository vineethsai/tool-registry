import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
import asyncio
import os
from fastapi import HTTPException
import unittest
from typing import Dict, List
import uuid

from tool_registry.main import app
from tool_registry.models import Agent, Tool, Policy, Credential, AccessLog

# Set TEST_MODE environment variable
os.environ["TEST_MODE"] = "true"

# Create a test client
@pytest.fixture
def client(
    mock_auth_and_agents,
    mock_authorization_service,
    mock_credential_vendor
):
    """Create a test client with mocked dependencies"""
    # Create the test client with the default auth header
    test_client = TestClient(app)
    test_client.headers = {"Authorization": "Bearer test_admin_token"}
    return test_client

@pytest.fixture
def test_admin_token():
    return "test_admin_token"

@pytest.fixture
def test_user_token():
    return "test_user_token"

@pytest.fixture
def test_admin_agent():
    return Agent(
        agent_id=UUID("00000000-0000-0000-0000-000000000001"),
        name="Admin Agent",
        description="Admin agent for testing",
        roles=["admin", "tool_publisher", "policy_admin"]
    )

@pytest.fixture
def test_user_agent():
    return Agent(
        agent_id=UUID("00000000-0000-0000-0000-000000000002"),
        name="User Agent",
        description="User agent for testing",
        roles=["user", "tester"]
    )

@pytest.fixture
def test_tool(test_admin_agent):
    return Tool(
        tool_id=UUID("00000000-0000-0000-0000-000000000003"),
        name="Test Tool",
        description="Test tool for integration testing",
        api_endpoint="https://api.example.com/test",
        auth_method="API_KEY",
        auth_config={"header_name": "X-API-Key"},
        params={"text": {"type": "string", "required": True}},
        version="1.0.0",
        owner_id=test_admin_agent.agent_id,
        tags=["test", "integration"],
        allowed_scopes=["read", "write", "execute"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_active=True
    )

@pytest.fixture
def test_policy():
    return Policy(
        policy_id=UUID("00000000-0000-0000-0000-000000000004"),
        name="Test Policy",
        description="Test policy for integration testing",
        rules={
            "roles": ["user", "tester", "admin"],
            "allowed_scopes": ["read", "write"],
            "max_credential_lifetime": 1800  # 30 minutes
        }
    )

@pytest.fixture
def mock_auth_and_agents(test_admin_agent, test_user_agent):
    """Patch authentication and agent management."""
    with patch('tool_registry.auth.authenticate_agent') as mock_auth:
        with patch('tool_registry.auth.get_current_agent') as mock_current_agent:
            with patch('tool_registry.auth.agents_db') as mock_agents_db:
                # Setup mock authentication
                async def mock_authenticate(username, password):
                    if username == "admin" and password == "admin_password":
                        return test_admin_agent
                    elif username == "user" and password == "user_password":
                        return test_user_agent
                    return None
                
                mock_auth.side_effect = mock_authenticate
                
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
                
                # Setup current agent
                async def get_agent_from_token(token):
                    if token == "test_admin_token":
                        return test_admin_agent
                    elif token == "test_user_token":
                        return test_user_agent
                    else:
                        raise Exception("Invalid token")
                
                # Mock the dependency
                mock_current_agent.side_effect = get_agent_from_token
                
                # Initialize test data in the database
                mock_agents_db[str(test_admin_agent.agent_id)] = test_admin_agent
                mock_agents_db[str(test_user_agent.agent_id)] = test_user_agent
                
                yield mock_auth, mock_current_agent, mock_agents_db

@pytest.fixture
def mock_tools_and_policies(test_tool, test_policy):
    """Patch the tools and policies storage."""
    with patch('tool_registry.main.tools') as mock_tools:
        with patch('tool_registry.main.policies') as mock_policies:
            # Setup mock tools
            mock_tools.__getitem__.side_effect = lambda key: (
                test_tool if key == str(test_tool.tool_id) else None
            )
            
            mock_tools.get.side_effect = lambda key, default=None: (
                test_tool if key == str(test_tool.tool_id) else default
            )
            
            mock_tools.values.return_value = [test_tool]
            
            # Setup mock policies
            mock_policies.__getitem__.side_effect = lambda key: (
                test_policy if key == str(test_policy.policy_id) else None
            )
            
            mock_policies.get.side_effect = lambda key, default=None: (
                test_policy if key == str(test_policy.policy_id) else default
            )
            
            mock_policies.values.return_value = [test_policy]
            
            # Link policy to tool
            test_tool.policy_id = [test_policy.policy_id]
            
            # Inject test data into the main module
            mock_tools[str(test_tool.tool_id)] = test_tool
            mock_policies[str(test_policy.policy_id)] = test_policy
            
            yield mock_tools, mock_policies

@pytest.fixture
def mock_authorization_service():
    mock_service = MagicMock()
    
    async def evaluate_access(agent: Agent, tool: Tool) -> Dict:
        # Admin agents always get access
        if agent.is_admin:
            return {
                "granted": True,
                "reason": "Admin access granted",
                "scopes": ["read", "write", "execute"],
                "duration_minutes": 60
            }
            
        # Test user gets access with limited scopes
        if agent.agent_id == TEST_USER_ID:
            return {
                "granted": True,
                "reason": "Test user access granted",
                "scopes": ["read"],
                "duration_minutes": 30
            }
            
        return {
            "granted": False,
            "reason": "No applicable policies found",
            "scopes": [],
            "duration_minutes": 0
        }
    
    mock_service.evaluate_access = evaluate_access
    return mock_service

@pytest.fixture
def mock_credential_vendor():
    mock_vendor = MagicMock()
    
    async def generate_credential(agent: Agent, tool: Tool, scope: List[str], duration: timedelta) -> Dict:
        return {
            "credential_id": str(uuid.uuid4()),
            "agent_id": agent.agent_id,
            "tool_id": tool.tool_id,
            "token": "test-credential-token",
            "expires_at": (datetime.now() + duration).isoformat(),
            "scope": scope
        }
        
    mock_vendor.generate_credential = generate_credential
    return mock_vendor

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

def test_create_agent_endpoint(client, test_admin_token, mock_auth_and_agents):
    """Test creating a new agent."""
    # Test as admin (should succeed)
    new_agent_data = {
        "name": "New Agent",
        "description": "New agent for testing",
        "roles": ["user"]
    }
    
    # Extract mock functions and create a custom mock for this test
    _, mock_current_agent, _ = mock_auth_and_agents
    
    with patch('tool_registry.main.get_current_agent') as mock_current_user:
        # Make admin request return admin agent
        admin_agent = Agent(
            agent_id=UUID("00000000-0000-0000-0000-000000000001"),
            name="Admin Agent",
            roles=["admin", "tool_publisher", "policy_admin"]
        )
        
        async def get_mock_agent(token=None):
            if token == "test_admin_token" or token == f"Bearer {test_admin_token}":
                return admin_agent
            elif token == "user_token" or token == "Bearer user_token":
                return Agent(
                    agent_id=uuid4(),
                    name="Not Admin",
                    roles=["user"]
                )
            raise HTTPException(status_code=401, detail="Invalid token")
            
        mock_current_user.side_effect = get_mock_agent
    
        # Admin request
        response = client.post(
            "/agents",
            json=new_agent_data,
            params={"password": "new_password"},
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == new_agent_data["name"]
        assert result["description"] == new_agent_data["description"]
        assert result["roles"] == new_agent_data["roles"]
        
        # Non-admin request
        response = client.post(
            "/agents",
            json=new_agent_data,
            params={"password": "new_password"},
            headers={"Authorization": "Bearer user_token"}
        )
        
        # Accept either 401 or 403 since the test is about authorization failure
        assert response.status_code in [401, 403]

def test_register_tool_endpoint(client, test_admin_token, mock_auth_and_agents, mock_tools_and_policies):
    """Test registering a new tool."""
    # Test as tool publisher (should succeed)
    new_tool_data = {
        "name": "New Tool",
        "description": "New tool for testing",
        "api_endpoint": "https://api.example.com/newtool",
        "auth_method": "OAUTH2",
        "auth_config": {},
        "params": {},
        "version": "1.0.0",
        "owner": "test-owner",
        "tags": ["new", "test"],
        "allowed_scopes": ["read", "write"]
    }
    
    # Mock the tools dict to store the new tool
    mock_tools, _ = mock_tools_and_policies
    
    with patch('tool_registry.main.get_current_agent') as mock_current_user:
        # Make admin request return admin agent
        admin_agent = Agent(
            agent_id=UUID("00000000-0000-0000-0000-000000000001"),
            name="Admin Agent",
            roles=["admin", "tool_publisher", "policy_admin"]
        )
        
        # Non-publisher agent for the second test
        non_publisher_agent = Agent(
            agent_id=uuid4(),
            name="Not Publisher",
            roles=["user"]
        )
        
        async def get_mock_agent(token=None):
            if token == "test_admin_token" or token == f"Bearer {test_admin_token}":
                return admin_agent
            elif token == "user_token" or token == "Bearer user_token":
                return non_publisher_agent
            raise HTTPException(status_code=401, detail="Invalid token")
            
        mock_current_user.side_effect = get_mock_agent
    
        # Tool publisher request
        response = client.post(
            "/tools",
            json=new_tool_data,
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == new_tool_data["name"]
        assert result["description"] == new_tool_data["description"]
        
        # Non-publisher request
        response = client.post(
            "/tools",
            json=new_tool_data,
            headers={"Authorization": "Bearer user_token"}
        )
        
        # Accept either 401 or 403 since the test is about authorization failure
        assert response.status_code in [401, 403]

def test_list_tools_endpoint(client, test_user_token, mock_auth_and_agents, mock_tools_and_policies):
    """Test listing tools."""
    response = client.get(
        "/tools",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Test with tag filter
    response = client.get(
        "/tools",
        params={"tags": ["test"]},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert len(result) > 0
    assert all("test" in tool["tags"] for tool in result)

def test_get_tool_endpoint(client, test_user_token, mock_auth_and_agents, mock_tools_and_policies, test_tool):
    """Test getting a specific tool."""
    # Get the mock tools dictionary
    mock_tools, _ = mock_tools_and_policies
    
    # Make sure test_tool is in the mocked tools AND available in the main app
    mock_tools[str(test_tool.tool_id)] = test_tool
    
    with patch("tool_registry.main.tools", {str(test_tool.tool_id): test_tool}):
        with patch('tool_registry.main.get_current_agent') as mock_current_user:
            # Standard user agent
            user_agent = Agent(
                agent_id=UUID("00000000-0000-0000-0000-000000000002"),
                name="User Agent",
                roles=["user", "tester"]
            )
            
            async def get_mock_agent(token=None):
                if token == "test_user_token" or token == f"Bearer {test_user_token}":
                    return user_agent
                raise HTTPException(status_code=401, detail="Invalid token")
                
            mock_current_user.side_effect = get_mock_agent
            
            # Test valid tool ID
            response = client.get(
                f"/tools/{test_tool.tool_id}",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["name"] == test_tool.name
            assert result["description"] == test_tool.description
            
            # Test invalid tool ID
            invalid_id = uuid4()
            response = client.get(
                f"/tools/{invalid_id}",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 404

def test_create_policy_endpoint(client, test_admin_token, mock_auth_and_agents, mock_tools_and_policies):
    """Test creating a new policy."""
    # Test as policy admin (should succeed)
    new_policy_data = {
        "name": "New Policy",
        "description": "New policy for testing",
        "rules": {
            "roles": ["user"],
            "allowed_scopes": ["read"]
        }
    }
    
    with patch('tool_registry.main.get_current_agent') as mock_current_user:
        # Make admin request return admin agent
        admin_agent = Agent(
            agent_id=UUID("00000000-0000-0000-0000-000000000001"),
            name="Admin Agent",
            roles=["admin", "tool_publisher", "policy_admin"]
        )
        
        # Non-admin agent for the second test
        non_admin_agent = Agent(
            agent_id=uuid4(),
            name="Not Policy Admin",
            roles=["user"]
        )
        
        async def get_mock_agent(token=None):
            if token == "test_admin_token" or token == f"Bearer {test_admin_token}":
                return admin_agent
            elif token == "user_token" or token == "Bearer user_token":
                return non_admin_agent
            raise HTTPException(status_code=401, detail="Invalid token")
            
        mock_current_user.side_effect = get_mock_agent
    
        # Admin request
        response = client.post(
            "/policies",
            json=new_policy_data,
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == new_policy_data["name"]
        assert result["description"] == new_policy_data["description"]
        assert result["rules"] == new_policy_data["rules"]
        
        # Non-admin request
        response = client.post(
            "/policies",
            json=new_policy_data,
            headers={"Authorization": "Bearer user_token"}
        )
        
        # Accept either 401 or 403 since the test is about authorization failure
        assert response.status_code in [401, 403]

def test_tool_access_endpoint(client, test_user_token, test_user_agent, test_tool, mock_authorization_service, mock_credential_vendor):
    """Test that the tool access endpoint returns a credential for an authorized request."""
    import json
    import asyncio
    from unittest.mock import patch, MagicMock
    
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
    
    # Need to bypass JWT verification
    def mock_jwt_decode(token, key, algorithms, **kwargs):
        return {"sub": str(test_user_agent.agent_id)}
    
    # Setup the mocks properly
    with patch('tool_registry.auth.jwt.decode', side_effect=mock_jwt_decode):
        with patch('tool_registry.main.tools', {str(test_tool.tool_id): test_tool}):
            with patch('tool_registry.api.app.tool_registry.get_tool', return_value=future_tool):
                with patch('tool_registry.api.app.credential_vendor.generate_credential', return_value=future_credential):
                    with patch('tool_registry.main.credential_vendor.generate_credential') as mock_gen_cred:
                        # Set up the generate_credential mock to work with async calls
                        async_cred_future = asyncio.Future()
                        async_cred_future.set_result(credential)
                        mock_gen_cred.return_value = async_cred_future
                
                        # Make the request with proper authorization header
                        headers = {"Authorization": f"Bearer {test_user_token}"}
                        response = client.post(
                            f"/tools/{test_tool.tool_id}/access",
                            headers=headers,
                            json={"scopes": ["read", "write"]}
                        )
                
                        # Print the response for debugging
                        print(f"Headers sent: {headers}")
                        print(f"Response status: {response.status_code}")
                        print(f"Response content: {response.content.decode()}")
                
                        # Assert response
                        assert response.status_code == 200
                        response_data = json.loads(response.content)
                        assert "credential" in response_data
                        assert "credential_id" in response_data["credential"]
                        assert response_data["tool"]["tool_id"] == str(test_tool.tool_id)

def test_validate_access_endpoint(client, mock_credential_vendor):
    """Test validating credential token."""
    # Valid token
    response = client.get(
        f"/tools/{mock_credential_vendor.credential.tool_id}/validate-access",
        params={"token": mock_credential_vendor.credential.token}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is True
    assert result["agent_id"] == str(mock_credential_vendor.credential.agent_id)
    
    # Invalid token
    mock_credential_vendor.validate_credential.return_value = mock_credential_vendor.future_none
    
    response = client.get(
        f"/tools/{mock_credential_vendor.credential.tool_id}/validate-access",
        params={"token": "invalid-token"}
    )
    
    assert response.status_code == 401

def test_access_logs_endpoint(client, test_admin_token, mock_auth_and_agents, mock_authorization_service):
    """Test getting access logs."""
    with patch('tool_registry.main.get_current_agent') as mock_current_user:
        # Make admin request return admin agent
        admin_agent = Agent(
            agent_id=UUID("00000000-0000-0000-0000-000000000001"),
            name="Admin Agent",
            roles=["admin", "tool_publisher", "policy_admin"]
        )
        
        # Non-admin agent for the second test
        non_admin_agent = Agent(
            agent_id=uuid4(),
            name="Not Admin",
            roles=["user"]
        )
        
        async def get_mock_agent(token=None):
            if token == "test_admin_token" or token == f"Bearer {test_admin_token}":
                return admin_agent
            elif token == "user_token" or token == "Bearer user_token":
                return non_admin_agent
            raise HTTPException(status_code=401, detail="Invalid token")
            
        mock_current_user.side_effect = get_mock_agent
    
        # Admin request
        response = client.get(
            "/access-logs",
            headers={"Authorization": f"Bearer {test_admin_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        
        # Non-admin request
        response = client.get(
            "/access-logs",
            headers={"Authorization": "Bearer user_token"}
        )
        
        # Accept either 401 or 403 since the test is about authorization failure
        assert response.status_code in [401, 403]

def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "healthy" 