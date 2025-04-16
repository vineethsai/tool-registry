import pytest
import os
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tool_registry.api.app import app, get_db, tool_registry, auth_service, credential_vendor
from tool_registry.models.agent import Agent
from tool_registry.models.tool import Tool
from tool_registry.models.policy import Policy
from tool_registry.models.credential import Credential
from tool_registry.core.database import Base

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

class TestEndToEndFlow:
    """End-to-end integration tests for the Tool Registry system.
    
    These tests verify complete workflows from registration to tool usage.
    """
    
    @pytest.fixture(scope="function")
    def test_db(self):
        """Create a test database with all tables."""
        # Create an in-memory database for testing
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Override the dependency to use our test database
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
                
        app.dependency_overrides[get_db] = override_get_db
        
        yield TestingSessionLocal
        
        # Clean up
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.clear()
    
    @pytest.fixture(scope="function")
    def client(self, test_db):
        """Create a test client with all external dependencies patched."""
        # Setup test data and mock service calls
        with patch('tool_registry.api.app.auth_service') as mock_auth_service:
            with patch('tool_registry.api.app.tool_registry') as mock_tool_registry:
                with patch('tool_registry.api.app.credential_vendor') as mock_credential_vendor:
                    # Setup a test agent
                    test_agent_id = uuid.uuid4()
                    admin_agent_id = uuid.uuid4()
                    test_tool_id = uuid.uuid4()
                    test_policy_id = uuid.uuid4()
                    test_credential_id = uuid.uuid4()
                    
                    # Mock auth service
                    mock_auth_service.verify_token = AsyncMock()
                    # Create a user agent without setting is_admin directly
                    user_agent = Agent(
                        agent_id=test_agent_id,
                        name="Test User",
                        roles=["user"]  # is_admin property will return False based on roles
                    )
                    mock_auth_service.verify_token.return_value = user_agent
                    
                    # Mock admin verification and admin agent
                    admin_agent = Agent(
                        agent_id=admin_agent_id,
                        name="Admin User",
                        roles=["admin", "tool_publisher", "policy_admin"]  # is_admin property will return True
                    )
                    # Use side_effect function to determine admin status
                    mock_auth_service.is_admin = MagicMock(side_effect=lambda agent: "admin" in agent.roles)
                    
                    # Setup for user registration
                    async def mock_register_agent(*args, **kwargs):
                        return Agent(
                            agent_id=test_agent_id,
                            name="Test User",
                            roles=["user"]
                        )
                    
                    mock_auth_service.register_agent = AsyncMock(side_effect=mock_register_agent)
                    mock_auth_service.create_token = MagicMock(return_value="test_token")
                    
                    # Setup for tool registry operations
                    test_tool = Tool(
                        tool_id=test_tool_id,
                        name="Test Tool",
                        description="A tool for testing",
                        api_endpoint="https://api.example.com/test",
                        auth_method="API_KEY",
                        version="1.0.0",
                        owner_id=admin_agent_id
                    )
                    
                    async def mock_register_tool(*args, **kwargs):
                        return test_tool_id
                    
                    async def mock_get_tool(*args, **kwargs):
                        return {
                            "tool_id": str(test_tool_id),
                            "name": "Test Tool",
                            "description": "A tool for testing",
                            "api_endpoint": "https://api.example.com/test",
                            "auth_method": "API_KEY",
                            "version": "1.0.0",
                            "owner_id": str(admin_agent_id),
                            "metadata": {
                                "inputs": {"text": {"type": "string"}},
                                "outputs": {"result": {"type": "string"}}
                            }
                        }
                    
                    mock_tool_registry.register_tool = AsyncMock(side_effect=mock_register_tool)
                    mock_tool_registry.get_tool = AsyncMock(side_effect=mock_get_tool)
                    mock_tool_registry.list_tools = AsyncMock(return_value=[
                        {
                            "tool_id": str(test_tool_id),
                            "name": "Test Tool",
                            "description": "A tool for testing",
                            "version": "1.0.0"
                        }
                    ])
                    
                    # Setup credential vendor
                    test_credential = Credential(
                        credential_id=test_credential_id,
                        agent_id=test_agent_id,
                        tool_id=test_tool_id,
                        token="test_credential_token",
                        expires_at=datetime.utcnow() + timedelta(hours=1),
                        scope=["read"]
                    )
                    
                    async def mock_generate_credential(*args, **kwargs):
                        return test_credential
                    
                    mock_credential_vendor.generate_credential = AsyncMock(side_effect=mock_generate_credential)
                    mock_credential_vendor.validate_credential = MagicMock(return_value=test_credential)
                    
                    # Return the client
                    yield TestClient(app)
    
    @pytest.mark.asyncio
    async def test_complete_tool_usage_flow(self, client):
        """Test the complete flow from agent creation to tool access and usage."""
        # Step 1: Register a new agent
        registration_data = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": "test@example.com",
            "password": "secure_password",
            "name": "Test User",
            "organization": "Test Org"
        }
        
        register_response = client.post("/register", json=registration_data)
        assert register_response.status_code == 200
        register_result = register_response.json()
        assert "agent_id" in register_result
        assert "token" in register_result
        
        token = register_result["token"]
        
        # Step 2: List available tools
        tools_response = client.get(
            "/tools",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert tools_response.status_code == 200
        tools = tools_response.json()
        assert len(tools) > 0
        tool_id = tools[0]["tool_id"]
        
        # Step 3: Get details for a specific tool
        tool_details_response = client.get(
            f"/tools/{tool_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert tool_details_response.status_code == 200
        tool_details = tool_details_response.json()
        assert tool_details["tool_id"] == tool_id
        
        # Step 4: Request access to the tool
        access_response = client.post(
            f"/tools/{tool_id}/access",
            json={"scopes": ["read"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert access_response.status_code == 200
        access_result = access_response.json()
        assert "credential" in access_result
        assert "credential_id" in access_result["credential"]
        assert "token" in access_result["credential"]
        
        credential_token = access_result["credential"]["token"]
        
        # Step 5: Validate the credential
        validate_response = client.get(
            f"/tools/{tool_id}/validate-access",
            params={"token": credential_token}
        )
        assert validate_response.status_code == 200
        validate_result = validate_response.json()
        assert validate_result["valid"] is True
        
        # Step 6: Simulate using the tool with the credential
        # This would typically be an external call to the tool's API
        # Here we just verify the credential can be validated again
        validate_again_response = client.get(
            f"/tools/{tool_id}/validate-access",
            params={"token": credential_token}
        )
        assert validate_again_response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_tool_publisher_flow(self, client):
        """Test the complete flow for a tool publisher registering and managing a tool."""
        # Step 1: Login as an admin user (with tool publisher role)
        login_response = client.post(
            "/token",
            data={"username": "admin", "password": "admin_password"}
        )
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "access_token" in login_result
        
        admin_token = login_result["access_token"]
        
        # Step 2: Register a new tool
        tool_data = {
            "name": f"Tool {uuid.uuid4().hex[:8]}",
            "description": "A new test tool",
            "api_endpoint": "https://api.example.com/newtool",
            "auth_method": "API_KEY",
            "auth_config": {"header_name": "X-API-Key"},
            "version": "1.0.0",
            "tags": ["test", "integration"],
            "tool_metadata": {
                "schema_version": "1.0",
                "inputs": {"text": {"type": "string"}},
                "outputs": {"result": {"type": "string"}}
            }
        }
        
        register_tool_response = client.post(
            "/tools",
            json=tool_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert register_tool_response.status_code == 200
        tool_result = register_tool_response.json()
        assert "tool_id" in tool_result
        new_tool_id = tool_result["tool_id"]
        
        # Step 3: Create a policy for the tool
        policy_data = {
            "name": "Public Access Policy",
            "description": "Policy allowing public access to the tool",
            "tool_id": new_tool_id,
            "rules": {
                "roles": ["user"],
                "allowed_scopes": ["read"],
                "max_credential_lifetime": 3600
            }
        }
        
        create_policy_response = client.post(
            "/policies",
            json=policy_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_policy_response.status_code == 200
        policy_result = create_policy_response.json()
        assert "policy_id" in policy_result
        
        # Step 4: Verify the tool is listed in the registry
        list_tools_response = client.get(
            "/tools",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert list_tools_response.status_code == 200
        tools_list = list_tools_response.json()
        
        # Find our newly created tool
        found = False
        for tool in tools_list:
            if tool.get("tool_id") == new_tool_id:
                found = True
                break
        
        assert found, "Newly created tool was not found in the list of tools" 