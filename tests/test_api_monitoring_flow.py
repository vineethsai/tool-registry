import pytest
import time
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from tool_registry.api.app import app, get_db, rate_limiter
from tool_registry.core.database import Base
from tool_registry.models.agent import Agent
from tool_registry.models.tool import Tool
from tool_registry.core.rate_limit import RateLimiter
from tool_registry.core.monitoring import log_access

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

class TestAPIMonitoringAndRateLimiting:
    """Tests for API monitoring, access logging, and rate limiting.
    
    These tests verify that:
    1. API access is properly logged
    2. Rate limiting is enforced
    3. Monitoring events are correctly tracked
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
        test_agent = Agent(
            agent_id=uuid.uuid4(),
            name="Test User",
            description="User for monitoring tests",
            roles=["user"]
        )
        db_session.add(test_agent)
        
        # Create a test tool
        test_tool = Tool(
            tool_id=uuid.uuid4(),
            name="Monitored Tool",
            description="Tool for monitoring tests",
            api_endpoint="https://api.example.com/monitored",
            auth_method="API_KEY",
            auth_config={},  # Initialize auth_config
            params={},       # Initialize params
            version="1.0.0",
            tags=[],         # Initialize tags
            owner_id=test_agent.agent_id,  # Set owner_id to fix the integrity constraint
            allowed_scopes=[]  # Initialize allowed_scopes
        )
        db_session.add(test_tool)
        
        # Commit the test data
        db_session.commit()
        
        # Store IDs for use in tests
        self.test_agent_id = test_agent.agent_id
        self.test_tool_id = test_tool.tool_id
        
        db_session.close()
        
        yield TestingSessionLocal
        
        # Clean up
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.clear()
    
    @pytest.fixture(scope="function")
    def real_rate_limiter(self):
        """Create a real rate limiter instance with a low limit for testing."""
        # Create a rate limiter with a limit of 3 requests per 2 seconds
        # This makes it easier to test rate limiting
        return RateLimiter(redis_client=None, rate_limit=3, time_window=2)
    
    @pytest.fixture(scope="function")
    def setup_auth_mock(self):
        """Set up mock for authentication."""
        with patch('tool_registry.api.app.auth_service') as mock_auth:
            # Set up token verification
            async def mock_verify_token(token):
                if token == "test_token" or token == "Bearer test_token":
                    return Agent(
                        agent_id=self.test_agent_id,
                        name="Test User",
                        roles=["user"]  # is_admin property will be derived from roles
                    )
                return None
            
            mock_auth.verify_token = AsyncMock(side_effect=mock_verify_token)
            # Use side_effect to determine if agent is admin based on roles
            mock_auth.is_admin = MagicMock(side_effect=lambda agent: "admin" in agent.roles)
            
            yield mock_auth
    
    @pytest.fixture(scope="function")
    def setup_tool_registry_mock(self):
        """Set up mock for tool registry."""
        with patch('tool_registry.api.app.tool_registry') as mock_registry:
            async def mock_get_tool(tool_id):
                if str(tool_id) == str(self.test_tool_id):
                    return {
                        "tool_id": str(self.test_tool_id),
                        "name": "Monitored Tool",
                        "description": "Tool for monitoring tests",
                        "api_endpoint": "https://api.example.com/monitored",
                        "auth_method": "API_KEY",
                        "version": "1.0.0"
                    }
                return None
            
            mock_registry.get_tool = AsyncMock(side_effect=mock_get_tool)
            mock_registry.list_tools = AsyncMock(return_value=[
                {
                    "tool_id": str(self.test_tool_id),
                    "name": "Monitored Tool",
                    "description": "Tool for monitoring tests",
                    "version": "1.0.0"
                }
            ])
            
            yield mock_registry
    
    @pytest.fixture(scope="function")
    def setup_monitoring(self):
        """Set up mocks for monitoring components."""
        with patch('tool_registry.api.app.log_access') as mock_log_access:
            # Keep track of logged events
            self.logged_events = []
            
            async def mock_log(*args, **kwargs):
                event = {
                    "timestamp": datetime.utcnow(),
                    "agent_id": kwargs.get("agent_id"),
                    "tool_id": kwargs.get("tool_id"),
                    "action": kwargs.get("action"),
                    "success": kwargs.get("success", True),
                    "error_message": kwargs.get("error_message")
                }
                self.logged_events.append(event)
                return None
            
            mock_log_access.side_effect = mock_log
            
            yield mock_log_access
    
    @pytest.fixture(scope="function")
    def client(self, test_db, setup_auth_mock, setup_tool_registry_mock, setup_monitoring, real_rate_limiter):
        """Create a test client with all monitoring-related dependencies patched."""
        
        # Patch the rate limiter with our testing instance
        with patch('tool_registry.api.app.rate_limiter', real_rate_limiter):
            # Create and return the test client
            test_client = TestClient(app)
            yield test_client
    
    def test_api_access_logging(self, client):
        """Test that API access is properly logged."""
        # Make a request that should be logged
        response = client.get(
            "/tools",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        
        # Check that the access was logged
        assert len(self.logged_events) > 0
        
        # The last event should be our request
        last_event = self.logged_events[-1]
        assert last_event["action"] == "list_tools"
        assert last_event["success"] is True
        
        # Make a request to a specific tool
        response = client.get(
            f"/tools/{self.test_tool_id}",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        
        # Check for the new log
        assert len(self.logged_events) > 1
        last_event = self.logged_events[-1]
        assert last_event["action"] == "get_tool"
        assert last_event["tool_id"] == str(self.test_tool_id)
    
    def test_error_logging(self, client):
        """Test that API errors are properly logged."""
        # Make a request to a non-existent tool
        non_existent_id = uuid.uuid4()
        response = client.get(
            f"/tools/{non_existent_id}",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 404
        
        # Check that the error was logged
        assert len(self.logged_events) > 0
        
        # Find the error event
        error_events = [event for event in self.logged_events 
                        if event["action"] == "get_tool" and event["success"] is False]
        
        assert len(error_events) > 0
        assert error_events[-1]["error_message"] is not None
    
    def test_rate_limiting(self, client):
        """Test that rate limiting is enforced."""
        # Make several requests in quick succession
        for i in range(3):
            response = client.get(
                "/tools",
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200
            assert "X-RateLimit-Remaining" in response.headers
            
            # Check the remaining count decreases
            remaining = int(response.headers["X-RateLimit-Remaining"])
            assert remaining == 2 - i
        
        # The next request should be rate-limited
        response = client.get(
            "/tools",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        
        # Wait for the rate limit window to reset
        time.sleep(2.1)
        
        # After waiting, requests should be allowed again
        response = client.get(
            "/tools",
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
    
    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are included in responses."""
        response = client.get(
            "/tools",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        
        # Check for the presence of rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify the header values
        assert int(response.headers["X-RateLimit-Limit"]) == 3  # Our test limiter
        assert int(response.headers["X-RateLimit-Remaining"]) == 2  # After one request
        
        # The reset time should be a future timestamp
        reset_time = response.headers["X-RateLimit-Reset"]
        assert reset_time is not None 