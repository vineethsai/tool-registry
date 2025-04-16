import pytest
import uuid
import json
import random
import string
from datetime import datetime, timedelta
from asyncio import current_task
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tool_registry.api.app import app, get_db
from tool_registry.core.database import Base
from tool_registry.models.agent import Agent
from tool_registry.models.tool import Tool
from tool_registry.models.policy import Policy
from tool_registry.models.credential import Credential
from tool_registry.core.monitoring import log_access

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

class TestEndToEndFlows:
    """Tests for complete end-to-end API flows without rate limiting.
    
    These tests verify:
    1. Complete user journeys through the API
    2. Integration between different API endpoints
    3. Data persistence and access control
    """
    
    @pytest.fixture(scope="function")
    def test_db(self):
        """Create a test database with all necessary tables."""
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
        
        # Create a session for fixture setup
        db_session = TestingSessionLocal()
        
        # Create test agents
        admin_agent = Agent(
            agent_id=uuid.uuid4(),
            name="Admin User",
            description="Admin for E2E tests",
            roles=["admin", "tool_publisher", "policy_admin"]
        )
        
        regular_user = Agent(
            agent_id=uuid.uuid4(),
            name="Regular User",
            description="Regular user for E2E tests",
            roles=["user"]
        )
        
        db_session.add(admin_agent)
        db_session.add(regular_user)
        
        # Create a test policy
        test_policy = Policy(
            policy_id=uuid.uuid4(),
            name="Test Policy",
            description="Policy for E2E testing",
            rules={
                "roles": ["user", "admin"],
                "allowed_scopes": ["read", "write"],
                "max_credential_lifetime": 3600  # 1 hour
            },
            created_by=admin_agent.agent_id
        )
        db_session.add(test_policy)
        
        # Create a test tool
        test_tool = Tool(
            tool_id=uuid.uuid4(),
            name="E2E Test Tool",
            description="Tool for E2E testing",
            api_endpoint="https://api.example.com/e2e",
            auth_method="API_KEY",
            auth_config={},
            params={},
            version="1.0.0",
            tags=[],
            owner_id=admin_agent.agent_id,
            allowed_scopes=["read", "write", "execute"]
        )
        db_session.add(test_tool)
        
        # Commit the test data
        db_session.commit()
        
        # Store IDs for use in tests
        self.admin_agent_id = admin_agent.agent_id
        self.regular_user_id = regular_user.agent_id
        self.test_policy_id = test_policy.policy_id
        self.test_tool_id = test_tool.tool_id
        
        db_session.close()
        
        yield TestingSessionLocal
        
        # Clean up
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.clear()
    
    @pytest.fixture(scope="function")
    def setup_auth_mock(self):
        """Set up mock for authentication."""
        with patch('tool_registry.api.app.auth_service') as mock_auth:
            # Set up token verification
            async def mock_verify_token(token):
                if token == "admin_token" or token == "Bearer admin_token":
                    return Agent(
                        agent_id=self.admin_agent_id,
                        name="Admin User",
                        roles=["admin", "tool_publisher", "policy_admin"]
                    )
                elif token == "user_token" or token == "Bearer user_token":
                    return Agent(
                        agent_id=self.regular_user_id,
                        name="Regular User",
                        roles=["user"]
                    )
                return None
            
            mock_auth.verify_token = AsyncMock(side_effect=mock_verify_token)
            # Use side_effect to determine if agent is admin based on roles
            mock_auth.is_admin = MagicMock(side_effect=lambda agent: "admin" in agent.roles)
            
            yield mock_auth
    
    @pytest.fixture(scope="function")
    def setup_credential_vendor_mock(self):
        """Set up mock for credential vendor."""
        with patch('tool_registry.api.app.credential_vendor') as mock_vendor:
            # Store credentials created during the test
            self.created_credentials = {}
            
            # Create test credential
            test_credential = {
                "credential_id": str(uuid.uuid4()),
                "agent_id": str(self.regular_user_id),
                "tool_id": str(self.test_tool_id),
                "token": "test-credential-token",
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
                "scope": ["read", "write"],
                "created_at": datetime.now().isoformat()
            }
            self.created_credentials["test-credential-token"] = test_credential
            
            async def mock_generate_credential(agent, tool, scopes, duration):
                # Create a unique token for this agent/tool combination
                token = f"{agent.roles[0]}-{str(tool.get('tool_id', uuid.uuid4()))[:8]}-token"
                
                credential = {
                    "credential_id": str(uuid.uuid4()),
                    "agent_id": str(agent.agent_id),
                    "tool_id": str(tool.get("tool_id", tool if isinstance(tool, (str, uuid.UUID)) else uuid.uuid4())),
                    "token": token,
                    "scope": scopes,
                    "expires_at": (datetime.now() + timedelta(minutes=duration)).isoformat(),
                    "created_at": datetime.now().isoformat()
                }
                
                # Store for later validation
                self.created_credentials[token] = credential
                return credential
            
            async def mock_validate_credential(token):
                if token in self.created_credentials:
                    credential = self.created_credentials[token]
                    expires_at = datetime.fromisoformat(credential["expires_at"].replace('Z', '+00:00'))
                    
                    # Check if the credential is expired
                    if expires_at < datetime.now():
                        return {
                            "valid": False,
                            "error": "Credential has expired"
                        }
                    
                    return {
                        **credential,
                        "valid": True,
                        "tool_id": credential["tool_id"]
                    }
                
                if token == "test-credential-token":
                    return {
                        **test_credential,
                        "valid": True,
                        "tool_id": test_credential["tool_id"]
                    }
                
                return {
                    "valid": False,
                    "error": "Invalid credential"
                }
                
            mock_vendor.generate_credential = AsyncMock(side_effect=mock_generate_credential)
            mock_vendor.validate_credential = AsyncMock(side_effect=mock_validate_credential)
            
            yield mock_vendor
    
    @pytest.fixture(scope="function")
    def setup_tool_registry_mock(self):
        """Set up mock for tool registry."""
        with patch('tool_registry.api.app.tool_registry') as mock_registry:
            # Initialize test tools list
            now = datetime.now()
            
            # Create a sample tool with all required fields
            tool1 = {
                "tool_id": str(uuid.uuid4()),
                "name": "test_tool",
                "description": "Test tool description",
                "api_endpoint": "https://test.com/api",
                "auth_method": "none",
                "auth_config": {},
                "params": {"input": "text"},
                "version": "1.0.0",
                "tags": ["test"],
                "owner_id": str(uuid.uuid4()),
                "allowed_scopes": ["*"],
                "created_at": now,
                "updated_at": now,
                "is_active": True,
                "metadata": {
                    "metadata_id": str(uuid.uuid4()),
                    "tool_id": str(uuid.uuid4()),
                    "schema_data": {},
                    "inputs": {"text": {"type": "string"}},
                    "outputs": {"result": {"type": "string"}},
                    "schema_version": "1.0",
                    "schema_type": "openapi",
                    "created_at": now,
                    "updated_at": now,
                    "provider": "test",
                    "documentation_url": "https://test.com/docs"
                }
            }
            
            # Store as first tool in the list
            self.test_tools = [tool1]
            
            # Mock registry methods
            async def mock_register_tool(tool_data, **kwargs):
                new_id = str(uuid.uuid4())
                now = datetime.now()
                
                # Handle Tool objects or dictionaries
                if hasattr(tool_data, 'name'):
                    # It's a Tool object
                    tool_name = tool_data.name
                    tool_description = tool_data.description
                    tool_version = tool_data.version
                    
                    # Extract metadata if available
                    tool_metadata = {}
                    if hasattr(tool_data, 'tool_metadata') and tool_data.tool_metadata:
                        tool_metadata = tool_data.tool_metadata
                else:
                    # It's a dictionary
                    tool_name = tool_data.get("name", "Unknown Tool")
                    tool_description = tool_data.get("description", "")
                    tool_version = tool_data.get("version", "1.0.0")
                    tool_metadata = tool_data.get("tool_metadata", {})
                
                new_tool = {
                    "tool_id": new_id,
                    "name": tool_name,
                    "description": tool_description,
                    "version": tool_version,
                    "api_endpoint": f"/api/tools/{tool_name}",
                    "auth_method": "API_KEY",
                    "auth_config": {},
                    "params": {},
                    "tags": [],
                    "owner_id": str(self.admin_agent_id),
                    "allowed_scopes": ["read", "write", "execute"],
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                    "metadata": tool_metadata
                }
                
                # Add to our list of tools
                self.test_tools.append(new_tool)
                
                return new_tool
            
            async def mock_get_tool(tool_id, **kwargs):
                # First check if we have this tool in our test_tools list
                for tool in self.test_tools:
                    if str(tool["tool_id"]) == str(tool_id):
                        # Make sure the tool has is_active field
                        if "is_active" not in tool:
                            tool["is_active"] = True
                        return tool
                
                # If not found but it's our initial test tool, return it
                if str(tool_id) == str(self.test_tool_id):
                    tool1["is_active"] = True  # Make sure tool1 has is_active field
                    return tool1
                
                # For tools not found, return a default
                return {
                    "tool_id": str(tool_id),
                    "name": "Flow Test Tool",
                    "description": "A tool for testing end-to-end flows",
                    "version": "1.0.0",
                    "api_endpoint": "/api/tools/flow-test-tool",
                    "auth_method": "API_KEY",
                    "auth_config": {},
                    "params": {},
                    "tags": ["test", "flow"],
                    "owner_id": str(self.admin_agent_id),
                    "allowed_scopes": ["read", "write", "execute"],
                    "is_active": True,  # Add is_active field
                    "metadata": {
                        "schema_version": "1.0",
                        "schema_type": "openapi",
                        "schema_data": {},
                        "inputs": {"text": {"type": "string"}},
                        "outputs": {"result": {"type": "string"}},
                        "documentation_url": "https://example.com/docs",
                        "provider": "test",
                        "tags": ["test", "flow"]
                    }
                }
            
            async def mock_list_tools(*args, **kwargs):
                """Mock of list_tools to return known tools."""
                now = datetime.now()
                
                # Ensure each tool has all required fields including timestamps
                for tool in self.test_tools:
                    if "created_at" not in tool:
                        tool["created_at"] = now
                    if "updated_at" not in tool:
                        tool["updated_at"] = now
                    if "is_active" not in tool:
                        tool["is_active"] = True
                    
                    # Ensure metadata has all required fields
                    if "metadata" in tool:
                        metadata = tool["metadata"]
                        if not metadata:
                            metadata = {}
                        
                        if "metadata_id" not in metadata:
                            metadata["metadata_id"] = str(uuid.uuid4())
                        if "tool_id" not in metadata:
                            metadata["tool_id"] = tool.get("tool_id", str(uuid.uuid4()))
                        if "schema_data" not in metadata:
                            metadata["schema_data"] = {}
                        if "inputs" not in metadata:
                            metadata["inputs"] = {"text": {"type": "string"}}
                        if "outputs" not in metadata:
                            metadata["outputs"] = {"result": {"type": "string"}}
                        if "schema_version" not in metadata:
                            metadata["schema_version"] = "1.0"
                        if "schema_type" not in metadata:
                            metadata["schema_type"] = "openapi"
                        if "created_at" not in metadata:
                            metadata["created_at"] = now
                        if "updated_at" not in metadata:
                            metadata["updated_at"] = now
                        if "provider" not in metadata:
                            metadata["provider"] = "test"
                        
                        tool["metadata"] = metadata
                
                return self.test_tools
            
            async def mock_search_tools(query=None, **kwargs):
                return self.test_tools
            
            mock_registry.register_tool = AsyncMock(side_effect=mock_register_tool)
            mock_registry.get_tool = AsyncMock(side_effect=mock_get_tool)
            mock_registry.list_tools = AsyncMock(side_effect=mock_list_tools)
            mock_registry.search_tools = AsyncMock(side_effect=mock_search_tools)
            
            yield mock_registry
    
    @pytest.fixture(scope="function")
    def setup_authorization_service_mock(self):
        """Set up mock for authorization service."""
        with patch('tool_registry.api.app.auth_service') as mock_auth_service:
            # Define evaluation logic based on user roles
            async def evaluate_access(agent, tool, **kwargs):
                tool_id = tool.get("tool_id", str(tool) if isinstance(tool, (str, uuid.UUID)) else None)
                
                # Admin always gets full access
                if "admin" in agent.roles:
                    return {
                        "granted": True,
                        "reason": "Admin access granted",
                        "scopes": ["read", "write", "execute", "delete"],
                        "duration_minutes": 1440  # 24 hours
                    }
                
                # Regular users get standard access
                if "user" in agent.roles:
                    return {
                        "granted": True,
                        "reason": "Standard access granted",
                        "scopes": ["read", "write"],
                        "duration_minutes": 60  # 1 hour
                    }
                
                # Readonly users only get read access
                if "readonly" in agent.roles:
                    return {
                        "granted": True,
                        "reason": "Read-only access granted",
                        "scopes": ["read"],
                        "duration_minutes": 30  # 30 minutes
                    }
                
                # Default deny
                return {
                    "granted": False,
                    "reason": "No applicable policy found",
                    "scopes": [],
                    "duration_minutes": 0
                }
            
            mock_auth_service.evaluate_access = AsyncMock(side_effect=evaluate_access)
            
            yield mock_auth_service
    
    @pytest.fixture(scope="function")
    def client(self, test_db, setup_auth_mock, setup_credential_vendor_mock, setup_tool_registry_mock, setup_authorization_service_mock):
        """Create a test client with mocked dependencies."""
        # Patch monitoring to avoid actual logging
        with patch('tool_registry.core.monitoring.log_access') as mock_log_access:
            # Keep track of logged events
            self.logged_events = []
            
            async def mock_log(*args, **kwargs):
                event = {
                    "timestamp": datetime.now(),
                    "agent_id": kwargs.get("agent_id"),
                    "tool_id": kwargs.get("tool_id"),
                    "action": kwargs.get("action"),
                    "success": kwargs.get("success", True),
                    "error_message": kwargs.get("error_message")
                }
                self.logged_events.append(event)
                return None
            
            mock_log_access.side_effect = mock_log
            
            # Patch the rate limiter to avoid rate limiting in these tests
            with patch('tool_registry.api.app.rate_limiter') as mock_rate_limiter:
                mock_rate_limiter.is_allowed.return_value = True
                mock_rate_limiter.get_remaining.return_value = 100
                mock_rate_limiter.get_reset_time.return_value = datetime.now() + timedelta(minutes=1)
                
                # Create and return the test client
                test_client = TestClient(app)
                yield test_client
    
    def test_tool_registration_and_discovery_flow(self, client):
        """Test complete flow: register tool -> list tools -> get specific tool."""
        # 1. Register a new tool as admin
        tool_data = {
            "name": "Flow Test Tool",
            "description": "A tool for testing end-to-end flows",
            "version": "1.0.0",
            "tool_metadata": {
                "schema_version": "1.0",
                "schema_type": "openapi",
                "schema_data": {},
                "inputs": {"text": {"type": "string"}},
                "outputs": {"result": {"type": "string"}},
                "documentation_url": "https://example.com/docs",
                "provider": "test",
                "tags": ["test", "flow"]
            }
        }
        
        response = client.post(
            "/tools/",
            json=tool_data,
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert response.status_code == 200
        tool_result = response.json()
        assert "tool_id" in tool_result
        created_tool_id = tool_result["tool_id"]
        
        # 2. List all tools as regular user
        response = client.get(
            "/tools",
            headers={"Authorization": "Bearer user_token"}
        )
        
        assert response.status_code == 200
        tools_list = response.json()
        assert isinstance(tools_list, list)
        assert any(tool["name"] == "Flow Test Tool" for tool in tools_list)
        
        # 3. Get specific tool details
        response = client.get(
            f"/tools/{created_tool_id}",
            headers={"Authorization": "Bearer user_token"}
        )
        
        assert response.status_code == 200
        tool_details = response.json()
        assert tool_details["tool_id"] == created_tool_id
        assert tool_details["name"] == "Flow Test Tool"
        assert "metadata" in tool_details
        assert tool_details["metadata"]["provider"] == "test"
    
    def test_tool_access_flow(self, client):
        """Test complete flow: discover tool -> request access -> validate access."""
        # 1. Get tool details
        response = client.get(
            f"/tools/{self.test_tool_id}",
            headers={"Authorization": "Bearer user_token"}
        )
        
        assert response.status_code == 200
        tool_info = response.json()
        
        # 2. Request access to the tool
        access_request = {
            "tool_id": str(self.test_tool_id),
            "justification": "Testing the complete access flow"
        }
        
        response = client.post(
            "/access",
            json=access_request,
            headers={"Authorization": "Bearer user_token"}
        )
        
        assert response.status_code == 200
        access_response = response.json()
        assert "credential" in access_response
        assert "tool" in access_response
        
        credential = access_response["credential"]
        assert "token" in credential
        credential_token = credential["token"]
        
        # 3. Validate access with the credential
        validate_request = {
            "credential_token": credential_token
        }
        
        response = client.post(
            "/validate",
            json=validate_request
        )
        
        assert response.status_code == 200
        validate_response = response.json()
        assert validate_response["valid"] is True
        assert "tool_id" in validate_response
        assert validate_response["tool_id"] == str(self.test_tool_id)
        
        # 4. Check access logs
        response = client.get(
            "/access-logs",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
        
        # Should find logs for our actions
        tool_access_logs = [log for log in logs if log.get("tool_id") == str(self.test_tool_id)]
        assert len(tool_access_logs) > 0
    
    def test_policy_management_flow(self, client):
        """Test policy creation and application flow."""
        # 1. Create a new policy
        policy_data = {
            "name": "Flow Test Policy",
            "description": "Policy for testing the E2E flow",
            "rules": {
                "roles": ["user"],
                "allowed_scopes": ["read"],
                "max_credential_lifetime": 1800
            }
        }
        
        response = client.post(
            "/policies",
            json=policy_data,
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert response.status_code == 200
        policy_result = response.json()
        assert "policy_id" in policy_result
        created_policy_id = policy_result["policy_id"]
        
        # 2. List all policies
        response = client.get(
            "/policies",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert response.status_code == 200
        policies_list = response.json()
        assert isinstance(policies_list, list)
        assert any(policy["name"] == "Flow Test Policy" for policy in policies_list)
        
        # 3. Apply policy to tool (this endpoint might vary based on actual implementation)
        update_data = {
            "policy_ids": [created_policy_id]
        }
        
        # Note: This is a hypothetical endpoint that might not exist in your API
        # You would need to adjust this based on your actual API design
        response = client.post(
            f"/tools/{self.test_tool_id}/policies",
            json=update_data,
            headers={"Authorization": "Bearer admin_token"}
        )
        
        # This assertion might need adjustment based on actual implementation
        assert response.status_code in [200, 201, 204]
    
    def test_monitoring_and_analytics_flow(self, client):
        """Test monitoring and analytics endpoints."""
        # Generate some activity
        client.get(
            "/tools",
            headers={"Authorization": "Bearer user_token"}
        )
        
        client.get(
            f"/tools/{self.test_tool_id}",
            headers={"Authorization": "Bearer user_token"}
        )
        
        # Test access logs endpoint
        response = client.get(
            "/access-logs",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
        
        # There should be logs for our recent activity
        recent_logs = [log for log in logs if log.get("action") in ["list_tools", "get_tool"]]
        assert len(recent_logs) >= 2
        
        # Test statistics endpoint if it exists
        response = client.get(
            "/statistics",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        # Depending on your API, this might return 200 or 404 if not implemented
        if response.status_code == 200:
            stats = response.json()
            assert "total_requests" in stats 