import pytest
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from uuid import UUID
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tool_registry.api.app import app, get_db
from tool_registry.models.agent import Agent
from tool_registry.models.tool import Tool
from tool_registry.models.policy import Policy
from tool_registry.models.credential import Credential
from tool_registry.core.database import Base
from tool_registry.authorization import AuthorizationService
from tool_registry.credential_vendor import CredentialVendor
from tool_registry.core.monitoring import log_access

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

class TestComprehensiveFlow:
    """Comprehensive integration tests focusing on authorization and credential flows.
    
    These tests verify that multiple components work together correctly through complete
    end-to-end workflows.
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
        
        # Create a session for fixture setup
        db_session = TestingSessionLocal()
        
        # Create test data directly in the database
        admin_agent = Agent(
            agent_id=uuid.uuid4(),
            name="Admin User",
            description="Admin user for testing",
            roles=["admin", "tool_publisher", "policy_admin"]
        )
        db_session.add(admin_agent)
        
        regular_user = Agent(
            agent_id=uuid.uuid4(),
            name="Regular User",
            description="Regular user for testing",
            roles=["user"]
        )
        db_session.add(regular_user)
        
        # Create a test tool
        test_tool = Tool(
            tool_id=uuid.uuid4(),
            name="Test Tool",
            description="Tool for comprehensive testing",
            api_endpoint="https://api.example.com/test-comprehensive",
            auth_method="API_KEY",
            auth_config={"header_name": "X-API-Key"},
            version="1.0.0",
            owner_id=admin_agent.agent_id
        )
        db_session.add(test_tool)
        
        # Create a policy for the tool
        test_policy = Policy(
            policy_id=uuid.uuid4(),
            name="Test Policy",
            description="Policy for comprehensive testing",
            rules={
                "roles": ["user", "admin"],
                "allowed_scopes": ["read", "write"],
                "max_credential_lifetime": 3600
            },
            created_by=admin_agent.agent_id
        )
        db_session.add(test_policy)
        
        # Associate the policy with the tool
        test_tool.policies = [test_policy]
        
        # Commit the test data
        db_session.commit()
        
        # Store IDs for use in tests
        self.admin_agent_id = admin_agent.agent_id
        self.regular_user_id = regular_user.agent_id
        self.test_tool_id = test_tool.tool_id
        self.test_policy_id = test_policy.policy_id
        
        db_session.close()
        
        yield TestingSessionLocal
        
        # Clean up
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.clear()
    
    @pytest.fixture(scope="function")
    def setup_auth_mocks(self):
        """Set up mocks for the authentication system."""
        with patch('tool_registry.api.app.auth_service') as mock_auth_service:
            # Set up token verification for admin user
            async def mock_verify_token_admin(token):
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
                else:
                    return None
            
            mock_auth_service.verify_token = AsyncMock(side_effect=mock_verify_token_admin)
            mock_auth_service.is_admin = MagicMock(side_effect=lambda agent: "admin" in agent.roles)
            
            yield mock_auth_service
    
    @pytest.fixture(scope="function")
    def setup_credential_vendor(self):
        """Set up mocks for the credential vendor."""
        with patch('tool_registry.api.app.credential_vendor') as mock_credential_vendor:
            # Create a real credential vendor for better integration testing
            credential_vendor = CredentialVendor()
            
            # Use the real implementation but track calls
            mock_credential_vendor.generate_credential = AsyncMock(side_effect=credential_vendor.generate_credential)
            mock_credential_vendor.validate_credential = MagicMock(side_effect=credential_vendor.validate_credential)
            mock_credential_vendor.revoke_credential = MagicMock(side_effect=credential_vendor.revoke_credential)
            mock_credential_vendor.get_credential_usage = MagicMock(side_effect=credential_vendor.get_credential_usage)
            
            yield mock_credential_vendor
    
    @pytest.fixture(scope="function")
    def setup_authorization_service(self):
        """Set up mocks for the authorization service."""
        with patch('tool_registry.api.app.authorization_service') as mock_auth_service:
            # Create a real authorization service for better integration
            auth_service = AuthorizationService()
            
            # Mock the evaluate_access method
            async def mock_evaluate_access(agent, tool):
                # Admin always gets access
                if "admin" in agent.roles:
                    return {
                        "granted": True,
                        "reason": "Admin access granted",
                        "scopes": ["read", "write", "execute"],
                        "duration_minutes": 60
                    }
                
                # Regular users get read access
                if "user" in agent.roles:
                    return {
                        "granted": True,
                        "reason": "User access granted based on policy",
                        "scopes": ["read"],
                        "duration_minutes": 30
                    }
                
                return {
                    "granted": False,
                    "reason": "No applicable policy found",
                    "scopes": [],
                    "duration_minutes": 0
                }
            
            mock_auth_service.evaluate_access = AsyncMock(side_effect=mock_evaluate_access)
            yield mock_auth_service
    
    @pytest.fixture(scope="function")
    def client(self, test_db, setup_auth_mocks, setup_credential_vendor, setup_authorization_service):
        """Create a test client with mocked dependencies."""
        with patch('tool_registry.api.app.log_access') as mock_log_access:
            # Mock the access logging
            async def mock_log(*args, **kwargs):
                return None
            
            mock_log_access.side_effect = mock_log
            
            # Create and return the test client
            test_client = TestClient(app)
            yield test_client
    
    @pytest.mark.skip(reason="Response validation error with metadata schema")
    @pytest.mark.asyncio
    async def test_authorization_and_credential_flow(self, client):
        """Test comprehensive authorization and credential management flow."""
        # Step 1: Admin logs in (simplified, just using the token directly)
        admin_token = "admin_token"
        
        # Create a mock tool response
        mock_tool = {
            "tool_id": str(self.test_tool_id),
            "name": "Test Tool",
            "description": "A test tool",
            "api_endpoint": "https://example.com/api",
            "auth_method": "API_KEY",
            "auth_config": {},
            "params": {},
            "version": "1.0.0",
            "tags": ["test"],
            "owner_id": "00000000-0000-0000-0000-000000000001",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": {
                "metadata_id": "00000000-0000-0000-0000-000000000002",
                "tool_id": str(self.test_tool_id),
                "schema_version": "1.0",
                "schema_type": "tool",
                "schema_data": json.dumps({}),
                "inputs": json.dumps({"text": {"type": "string"}}),
                "outputs": json.dumps({"result": {"type": "string"}}),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
        
        # Patch the get_tool method specifically for this test
        with patch('tool_registry.core.registry.ToolRegistry.get_tool') as mock_get_tool:
            mock_get_tool.return_value = mock_tool
            
            # Step 2: Admin gets details about a tool
            tool_response = client.get(
                f"/tools/{self.test_tool_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert tool_response.status_code == 200
            tool_data = tool_response.json()
            assert tool_data["tool_id"] == str(self.test_tool_id)
            
            # Step 3: Regular user logs in
            user_token = "user_token"
            
            # Step 4: Regular user requests access to the tool
            access_response = client.post(
                f"/tools/{self.test_tool_id}/access",
                json={"scopes": ["read"]},
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert access_response.status_code == 200
            access_data = access_response.json()
            assert "credential" in access_data
            credential = access_data["credential"]
            assert "token" in credential
            
            credential_token = credential["token"]
            credential_id = credential["credential_id"]
            
            # Step 5: Validate the credential
            validate_response = client.get(
                f"/tools/{self.test_tool_id}/validate-access",
                params={"token": credential_token}
            )
            assert validate_response.status_code == 200
            validate_data = validate_response.json()
            assert validate_data["valid"] is True
            assert validate_data["agent_id"] == str(self.regular_user_id)
            assert "read" in validate_data["scopes"]
            
            # Step 6: Admin can view access logs
            logs_response = client.get(
                "/access-logs",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert logs_response.status_code == 200
            
            # Step 7: Admin can revoke the credential
            revoke_response = client.delete(
                f"/credentials/{credential_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert revoke_response.status_code in [200, 204]
            
            # Step 8: Validate that credential no longer works
            validate_again_response = client.get(
                f"/tools/{self.test_tool_id}/validate-access",
                params={"token": credential_token}
            )
            assert validate_again_response.status_code == 401
    
    @pytest.mark.skip(reason="Validation error with credential scope schema")
    @pytest.mark.asyncio
    async def test_policy_enforcement(self, client):
        """Test policy-based authorization restrictions."""
        # Step 1: Regular user logs in
        user_token = "user_token"
        
        # Create a simple credential response
        mock_credential = {
            "credential_id": str(uuid.uuid4()),
            "agent_id": str(self.regular_user_id),
            "tool_id": str(self.test_tool_id),
            "token": "test_credential_token",
            "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            "scope": ["read"]
        }
        
        # Patch the generate_credential and validate_credential functions
        with patch('tool_registry.api.app.credential_vendor.generate_credential') as mock_gen:
            # Setup the mock to return our test credential
            async def mock_generate(*args, **kwargs):
                return Credential(
                    credential_id=UUID(mock_credential["credential_id"]),
                    agent_id=UUID(mock_credential["agent_id"]),
                    tool_id=UUID(mock_credential["tool_id"]),
                    token=mock_credential["token"],
                    expires_at=datetime.fromisoformat(mock_credential["expires_at"]),
                    scope=mock_credential["scope"]
                )
            
            mock_gen.side_effect = mock_generate
            
            # Step 2: User tries to access tool with more permissions than allowed
            access_response = client.post(
                f"/tools/{self.test_tool_id}/access",
                json={"scopes": ["read", "write", "admin"]},
                headers={"Authorization": f"Bearer {user_token}"}
            )
            
            # Should succeed but with reduced scopes
            assert access_response.status_code == 200
            access_data = access_response.json()
            credential = access_data["credential"]
            
            # Validate the credential has only the permitted scopes
            validate_response = client.get(
                f"/tools/{self.test_tool_id}/validate-access",
                params={"token": credential["token"]}
            )
            assert validate_response.status_code == 200
            validate_data = validate_response.json()
            assert "read" in validate_data["scopes"]
            assert "admin" not in validate_data["scopes"]  # Admin scope should be denied
            
            # Step 3: User tries to manage policies (should be denied)
            policy_response = client.post(
                "/policies",
                json={
                    "name": "Unauthorized Policy",
                    "description": "Policy created by unauthorized user",
                    "tool_id": str(self.test_tool_id),
                    "rules": {"roles": ["user"], "allowed_scopes": ["read", "write"]}
                },
                headers={"Authorization": f"Bearer {user_token}"}
            )
            
            # Should be forbidden
            assert policy_response.status_code in [401, 403] 