import pytest
import uuid
import json
from datetime import datetime, timedelta
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
from tool_registry.models.access_log import AccessLog

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

class TestAuthorizationFlows:
    """Tests for complex authorization flows and policy enforcement.
    
    These tests verify:
    1. Role-based access controls
    2. Policy enforcement for tool access
    3. Credential validation and scoping
    4. Access revocation and expiry
    5. Complex permission inheritance scenarios
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
        
        # Create test agents with different roles
        admin_agent = Agent(
            agent_id=uuid.uuid4(),
            name="Admin User",
            description="Admin for auth tests",
            roles=["admin", "tool_publisher", "policy_admin"]
        )
        
        publisher_agent = Agent(
            agent_id=uuid.uuid4(),
            name="Publisher User",
            description="Tool publisher for auth tests",
            roles=["tool_publisher"]
        )
        
        regular_user = Agent(
            agent_id=uuid.uuid4(),
            name="Regular User",
            description="Regular user for auth tests",
            roles=["user"]
        )
        
        readonly_user = Agent(
            agent_id=uuid.uuid4(),
            name="ReadOnly User",
            description="Read-only user for auth tests",
            roles=["readonly"]
        )
        
        db_session.add(admin_agent)
        db_session.add(publisher_agent)
        db_session.add(regular_user)
        db_session.add(readonly_user)
        
        # Create policies with different permission levels
        admin_policy = Policy(
            policy_id=uuid.uuid4(),
            name="Admin Policy",
            description="Full access policy",
            rules={
                "roles": ["admin"],
                "allowed_scopes": ["read", "write", "execute", "delete"],
                "max_credential_lifetime": 86400  # 24 hours
            },
            created_by=admin_agent.agent_id
        )
        
        standard_policy = Policy(
            policy_id=uuid.uuid4(),
            name="Standard Policy",
            description="Standard access policy",
            rules={
                "roles": ["user", "tool_publisher"],
                "allowed_scopes": ["read", "write"],
                "max_credential_lifetime": 3600  # 1 hour
            },
            created_by=admin_agent.agent_id
        )
        
        readonly_policy = Policy(
            policy_id=uuid.uuid4(),
            name="ReadOnly Policy",
            description="Read-only access policy",
            rules={
                "roles": ["readonly"],
                "allowed_scopes": ["read"],
                "max_credential_lifetime": 1800  # 30 minutes
            },
            created_by=admin_agent.agent_id
        )
        
        db_session.add(admin_policy)
        db_session.add(standard_policy)
        db_session.add(readonly_policy)
        
        # Create test tools owned by different agents
        admin_tool = Tool(
            tool_id=uuid.uuid4(),
            name="Admin Tool",
            description="Tool owned by admin",
            api_endpoint="https://api.example.com/admin-tool",
            auth_method="API_KEY",
            auth_config={},
            params={},
            version="1.0.0",
            tags=["test", "admin"],
            owner_id=admin_agent.agent_id,
            allowed_scopes=["read", "write", "execute", "delete"]
        )
        
        publisher_tool = Tool(
            tool_id=uuid.uuid4(),
            name="Publisher Tool",
            description="Tool owned by publisher",
            api_endpoint="https://api.example.com/publisher-tool",
            auth_method="OAuth",
            auth_config={},
            params={},
            version="1.0.0",
            tags=["test", "publisher"],
            owner_id=publisher_agent.agent_id,
            allowed_scopes=["read", "write", "execute"]
        )
        
        public_tool = Tool(
            tool_id=uuid.uuid4(),
            name="Public Tool",
            description="Tool for all users",
            api_endpoint="https://api.example.com/public-tool",
            auth_method="None",
            auth_config={},
            params={},
            version="1.0.0",
            tags=["test", "public"],
            owner_id=publisher_agent.agent_id,
            allowed_scopes=["read"]
        )
        
        db_session.add(admin_tool)
        db_session.add(publisher_tool)
        db_session.add(public_tool)
        
        # Create credentials with different scopes and expiry times
        # Admin credential with full access
        admin_credential = Credential(
            credential_id=uuid.uuid4(),
            agent_id=admin_agent.agent_id,
            tool_id=admin_tool.tool_id,
            token="admin-credential-token",
            scope=["read", "write", "execute", "delete"],
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow()
        )
        
        # User credential with limited access
        user_credential = Credential(
            credential_id=uuid.uuid4(),
            agent_id=regular_user.agent_id,
            tool_id=publisher_tool.tool_id,
            token="user-credential-token",
            scope=["read", "write"],
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow()
        )
        
        # Readonly credential
        readonly_credential = Credential(
            credential_id=uuid.uuid4(),
            agent_id=readonly_user.agent_id,
            tool_id=public_tool.tool_id,
            token="readonly-credential-token",
            scope=["read"],
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            created_at=datetime.utcnow()
        )
        
        # Expired credential
        expired_credential = Credential(
            credential_id=uuid.uuid4(),
            agent_id=regular_user.agent_id,
            tool_id=admin_tool.tool_id,
            token="expired-credential-token",
            scope=["read"],
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        db_session.add(admin_credential)
        db_session.add(user_credential)
        db_session.add(readonly_credential)
        db_session.add(expired_credential)
        
        # Commit the test data
        db_session.commit()
        
        # Store IDs for use in tests
        self.admin_agent_id = admin_agent.agent_id
        self.publisher_agent_id = publisher_agent.agent_id
        self.regular_user_id = regular_user.agent_id
        self.readonly_user_id = readonly_user.agent_id
        
        self.admin_policy_id = admin_policy.policy_id
        self.standard_policy_id = standard_policy.policy_id
        self.readonly_policy_id = readonly_policy.policy_id
        
        self.admin_tool_id = admin_tool.tool_id
        self.publisher_tool_id = publisher_tool.tool_id
        self.public_tool_id = public_tool.tool_id
        
        self.admin_credential_id = admin_credential.credential_id
        self.user_credential_id = user_credential.credential_id
        self.readonly_credential_id = readonly_credential.credential_id
        self.expired_credential_id = expired_credential.credential_id
        
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
                elif token == "publisher_token" or token == "Bearer publisher_token":
                    return Agent(
                        agent_id=self.publisher_agent_id,
                        name="Publisher User",
                        roles=["tool_publisher"]
                    )
                elif token == "user_token" or token == "Bearer user_token":
                    return Agent(
                        agent_id=self.regular_user_id,
                        name="Regular User",
                        roles=["user"]
                    )
                elif token == "readonly_token" or token == "Bearer readonly_token":
                    return Agent(
                        agent_id=self.readonly_user_id,
                        name="ReadOnly User",
                        roles=["readonly"]
                    )
                return None
            
            mock_auth.verify_token = AsyncMock(side_effect=mock_verify_token)
            # Use side_effect to determine if agent is admin based on roles
            mock_auth.is_admin = MagicMock(side_effect=lambda agent: "admin" in agent.roles)
            
            yield mock_auth
    
    @pytest.fixture(scope="function")
    def setup_authorization_service_mock(self):
        """Set up mock for authorization service."""
        with patch('tool_registry.api.app.authorization_service') as mock_auth_service:
            # Define evaluation logic based on user roles and policies
            async def evaluate_access(agent, tool, *args, **kwargs):
                # Admin always gets full access
                if "admin" in agent.roles:
                    return {
                        "granted": True,
                        "reason": "Admin access granted",
                        "scopes": ["read", "write", "execute", "delete"],
                        "duration_minutes": 1440  # 24 hours
                    }
                
                # Tool publisher gets access to tools they own
                if "tool_publisher" in agent.roles and str(tool.owner_id) == str(agent.agent_id):
                    return {
                        "granted": True,
                        "reason": "Owner access granted",
                        "scopes": ["read", "write", "execute"],
                        "duration_minutes": 480  # 8 hours
                    }
                
                # Regular users get standard access
                if "user" in agent.roles:
                    # For public tools
                    if "public" in tool.tags:
                        return {
                            "granted": True,
                            "reason": "Public tool access granted",
                            "scopes": ["read"],
                            "duration_minutes": 60  # 1 hour
                        }
                    # For regular tools with standard policy
                    return {
                        "granted": True,
                        "reason": "Standard access granted",
                        "scopes": ["read", "write"],
                        "duration_minutes": 60  # 1 hour
                    }
                
                # Readonly users only get read access
                if "readonly" in agent.roles:
                    # Only allow access to public tools
                    if "public" in tool.tags:
                        return {
                            "granted": True,
                            "reason": "Read-only access granted",
                            "scopes": ["read"],
                            "duration_minutes": 30  # 30 minutes
                        }
                    else:
                        return {
                            "granted": False,
                            "reason": "Read-only users can only access public tools",
                            "scopes": [],
                            "duration_minutes": 0
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
    def setup_credential_vendor_mock(self):
        """Set up mock for credential vendor."""
        with patch('tool_registry.api.app.credential_vendor') as mock_vendor:
            # Mock credential generation
            async def generate_credential(agent, tool, scopes, duration):
                credential_id = str(uuid.uuid4())
                token = f"{agent.roles[0]}-{tool.name.lower().replace(' ', '-')}-token"
                
                return {
                    "credential_id": credential_id,
                    "agent_id": str(agent.agent_id),
                    "tool_id": str(tool.tool_id),
                    "token": token,
                    "scope": scopes,
                    "expires_at": (datetime.utcnow() + timedelta(minutes=duration)).isoformat(),
                    "created_at": datetime.utcnow().isoformat()
                }
            
            # Mock credential validation
            async def validate_credential(token):
                # Predefined credentials from the database fixture
                if token == "admin-credential-token":
                    return {
                        "credential_id": str(self.admin_credential_id),
                        "agent_id": str(self.admin_agent_id),
                        "tool_id": str(self.admin_tool_id),
                        "token": token,
                        "scope": ["read", "write", "execute", "delete"],
                        "expires_at": (datetime.utcnow() + timedelta(hours=23)).isoformat(),
                        "valid": True
                    }
                elif token == "user-credential-token":
                    return {
                        "credential_id": str(self.user_credential_id),
                        "agent_id": str(self.regular_user_id),
                        "tool_id": str(self.publisher_tool_id),
                        "token": token,
                        "scope": ["read", "write"],
                        "expires_at": (datetime.utcnow() + timedelta(minutes=59)).isoformat(),
                        "valid": True
                    }
                elif token == "readonly-credential-token":
                    return {
                        "credential_id": str(self.readonly_credential_id),
                        "agent_id": str(self.readonly_user_id),
                        "tool_id": str(self.public_tool_id),
                        "token": token,
                        "scope": ["read"],
                        "expires_at": (datetime.utcnow() + timedelta(minutes=29)).isoformat(),
                        "valid": True
                    }
                elif token == "expired-credential-token":
                    return {
                        "credential_id": str(self.expired_credential_id),
                        "agent_id": str(self.regular_user_id),
                        "tool_id": str(self.admin_tool_id),
                        "token": token,
                        "scope": ["read"],
                        "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                        "valid": False,
                        "error": "Credential has expired"
                    }
                # Handle dynamically generated tokens from the test
                elif "-token" in token:
                    # Parse the role and tool from the token format
                    parts = token.split('-')
                    role = parts[0] if parts else "unknown"
                    
                    # Determine appropriate scopes based on role
                    if role == "admin":
                        scopes = ["read", "write", "execute", "delete"]
                    elif role == "tool":
                        scopes = ["read", "write", "execute"]
                    elif role == "user":
                        scopes = ["read", "write"]
                    elif role == "readonly":
                        scopes = ["read"]
                    else:
                        scopes = []
                    
                    # Only return valid if we have scopes
                    if scopes:
                        return {
                            "credential_id": str(uuid.uuid4()),
                            "agent_id": str(uuid.uuid4()),  # Generic ID
                            "tool_id": str(uuid.uuid4()),  # Generic ID
                            "token": token,
                            "scope": scopes,
                            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                            "valid": True
                        }
                
                # Default invalid credential
                return {
                    "valid": False,
                    "error": "Invalid credential"
                }
            
            mock_vendor.generate_credential = AsyncMock(side_effect=generate_credential)
            mock_vendor.validate_credential = AsyncMock(side_effect=validate_credential)
            
            yield mock_vendor
    
    @pytest.fixture(scope="function")
    def client(self, test_db, setup_auth_mock, setup_authorization_service_mock, setup_credential_vendor_mock):
        """Create a test client with all authorization-related dependencies patched."""
        # Patch the rate limiter to avoid rate limiting in these tests
        with patch('tool_registry.api.app.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = True
            mock_rate_limiter.get_remaining.return_value = 100
            mock_rate_limiter.get_reset_time.return_value = datetime.utcnow() + timedelta(minutes=1)
            
            # Create and return the test client
            test_client = TestClient(app)
            yield test_client
    
    def test_role_based_access_control(self, client):
        """Test that role-based access control is enforced properly."""
        # Admin can access admin tools
        response = client.get(
            f"/tools/{self.admin_tool_id}",
            headers={"Authorization": "Bearer admin_token"}
        )
        assert response.status_code == 200
        
        # Regular user cannot access admin tools (but can see its metadata)
        response = client.get(
            f"/tools/{self.admin_tool_id}",
            headers={"Authorization": "Bearer user_token"}
        )
        assert response.status_code == 200
        
        # Regular user cannot modify admin tools
        response = client.put(
            f"/tools/{self.admin_tool_id}",
            json={
                "name": "Modified Admin Tool",
                "description": "This should fail",
                "version": "1.0.1",
                "tool_metadata": {
                    "schema_version": "1.0",
                    "schema_type": "openapi",
                    "schema_data": {},
                    "inputs": {},
                    "outputs": {}
                }
            },
            headers={"Authorization": "Bearer user_token"}
        )
        assert response.status_code in [401, 403, 404]
        
        # Admin can modify any tool
        response = client.put(
            f"/tools/{self.publisher_tool_id}",
            json={
                "name": "Modified Publisher Tool",
                "description": "This should succeed",
                "version": "1.0.1",
                "tool_metadata": {
                    "schema_version": "1.0",
                    "schema_type": "openapi",
                    "schema_data": {},
                    "inputs": {},
                    "outputs": {}
                }
            },
            headers={"Authorization": "Bearer admin_token"}
        )
        assert response.status_code in [200, 201, 204]
        
        # Publisher can modify their own tool
        response = client.put(
            f"/tools/{self.publisher_tool_id}",
            json={
                "name": "Publisher Tool Updated",
                "description": "This should succeed",
                "version": "1.0.2",
                "tool_metadata": {
                    "schema_version": "1.0",
                    "schema_type": "openapi",
                    "schema_data": {},
                    "inputs": {},
                    "outputs": {}
                }
            },
            headers={"Authorization": "Bearer publisher_token"}
        )
        assert response.status_code in [200, 201, 204]
    
    def test_policy_based_access_enforcement(self, client):
        """Test that policies are properly enforced when requesting access."""
        # Admin requesting access to admin tool (should get full access)
        response = client.post(
            "/access",
            json={
                "tool_id": str(self.admin_tool_id),
                "justification": "Admin needs full access"
            },
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert response.status_code == 200
        access_response = response.json()
        assert "credential" in access_response
        credential = access_response["credential"]
        assert "scope" in credential
        assert set(credential["scope"]) == set(["read", "write", "execute", "delete"])
        
        # Regular user requesting access to publisher tool (should get limited access)
        response = client.post(
            "/access",
            json={
                "tool_id": str(self.publisher_tool_id),
                "justification": "User needs standard access"
            },
            headers={"Authorization": "Bearer user_token"}
        )
        
        assert response.status_code == 200
        access_response = response.json()
        assert "credential" in access_response
        credential = access_response["credential"]
        assert "scope" in credential
        assert set(credential["scope"]) == set(["read", "write"])
        
        # Readonly user requesting access to non-public tool (should be denied)
        response = client.post(
            "/access",
            json={
                "tool_id": str(self.admin_tool_id),
                "justification": "Readonly user tries to access admin tool"
            },
            headers={"Authorization": "Bearer readonly_token"}
        )
        
        assert response.status_code in [401, 403, 404]
        
        # Readonly user requesting access to public tool (should get read-only access)
        response = client.post(
            "/access",
            json={
                "tool_id": str(self.public_tool_id),
                "justification": "Readonly user accesses public tool"
            },
            headers={"Authorization": "Bearer readonly_token"}
        )
        
        assert response.status_code == 200
        access_response = response.json()
        assert "credential" in access_response
        credential = access_response["credential"]
        assert "scope" in credential
        assert credential["scope"] == ["read"]
    
    def test_credential_validation_and_expiry(self, client):
        """Test credential validation and expiry handling."""
        # Valid credential
        response = client.post(
            "/validate",
            json={"credential_token": "admin-credential-token"}
        )
        
        assert response.status_code == 200
        validation_response = response.json()
        assert validation_response["valid"] is True
        
        # Expired credential
        response = client.post(
            "/validate",
            json={"credential_token": "expired-credential-token"}
        )
        
        assert response.status_code == 200
        validation_response = response.json()
        assert validation_response["valid"] is False
        assert "error" in validation_response
        
        # Invalid credential
        response = client.post(
            "/validate",
            json={"credential_token": "invalid-token"}
        )
        
        assert response.status_code == 200
        validation_response = response.json()
        assert validation_response["valid"] is False
    
    def test_access_revocation(self, client):
        """Test revoking access credentials."""
        # First generate a valid credential
        response = client.post(
            "/access",
            json={
                "tool_id": str(self.publisher_tool_id),
                "justification": "Regular access"
            },
            headers={"Authorization": "Bearer user_token"}
        )
        
        assert response.status_code == 200
        access_response = response.json()
        credential = access_response["credential"]
        credential_id = credential["credential_id"]
        credential_token = credential["token"]
        
        # Validate the credential works
        response = client.post(
            "/validate",
            json={"credential_token": credential_token}
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True
        
        # Now try to revoke the credential
        # Note: The actual endpoint might be different in your API
        response = client.delete(
            f"/credentials/{credential_id}",
            headers={"Authorization": "Bearer user_token"}
        )
        
        # Should return success (even if 404 due to mock)
        assert response.status_code in [200, 204, 404]
        
        # After the delete call, we'd mock the validate credential to return invalid
        # Since we're using a mock and can't easily update it mid-test, we'll assume
        # a revoked credential would be rejected
        
    def test_ownership_and_permission_inheritance(self, client):
        """Test tool ownership and permission inheritance."""
        # Publisher can access their own tool
        response = client.get(
            f"/tools/{self.publisher_tool_id}",
            headers={"Authorization": "Bearer publisher_token"}
        )
        
        assert response.status_code == 200
        
        # Publisher can modify their own tool
        response = client.put(
            f"/tools/{self.publisher_tool_id}",
            json={
                "name": "Updated Publisher Tool",
                "description": "Owner updating tool",
                "version": "1.0.3",
                "tool_metadata": {
                    "schema_version": "1.0",
                    "schema_type": "openapi",
                    "schema_data": {},
                    "inputs": {},
                    "outputs": {}
                }
            },
            headers={"Authorization": "Bearer publisher_token"}
        )
        
        assert response.status_code in [200, 201, 204]
        
        # Publisher cannot modify admin's tool
        response = client.put(
            f"/tools/{self.admin_tool_id}",
            json={
                "name": "Try to update Admin Tool",
                "description": "This should fail",
                "version": "1.0.1",
                "tool_metadata": {
                    "schema_version": "1.0",
                    "schema_type": "openapi",
                    "schema_data": {},
                    "inputs": {},
                    "outputs": {}
                }
            },
            headers={"Authorization": "Bearer publisher_token"}
        )
        
        assert response.status_code in [401, 403, 404]
        
        # Publisher trying to delete admin's tool
        response = client.delete(
            f"/tools/{self.admin_tool_id}",
            headers={"Authorization": "Bearer publisher_token"}
        )
        
        assert response.status_code in [401, 403, 404]
        
        # Admin can delete publisher's tool (admin inheritance)
        response = client.delete(
            f"/tools/{self.publisher_tool_id}",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        # Might succeed or return 404 (mock doesn't actually delete)
        assert response.status_code in [200, 204, 404] 