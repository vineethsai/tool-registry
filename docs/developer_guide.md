# Developer Guide

This guide is intended for developers who want to extend, customize, or contribute to the GenAI Tool Registry.

## Project Structure

The project is organized into the following directories:

- `tool_registry/`: Main package directory
  - `api/`: API endpoints and FastAPI application
  - `auth/`: Authentication and authorization components
  - `core/`: Core functionality (registry, database, etc.)
  - `examples/`: Example usage and demo applications
  - `utils/`: Utility functions and helpers

## Design Principles

The GenAI Tool Registry follows these design principles:

1. **Modularity**: Components are designed to be modular and replaceable.
2. **Type Safety**: Type hints are used throughout the codebase.
3. **API-First**: The API is designed to be easy to use and understand.
4. **Security**: Security is a primary consideration in all design decisions.
5. **Extensibility**: The system is designed to be extended with new functionality.

## Core Components

### Database Schema

The database schema is defined using SQLAlchemy ORM:

```python
# tool_registry/core/database.py

from sqlalchemy import Column, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class Tool(Base):
    __tablename__ = "tools"
    
    tool_id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    version = Column(String)
    endpoint = Column(String)
    auth_required = Column(Boolean, default=True)
    # ... other fields
```

### Registry Service

The registry service manages tools in the system:

```python
# tool_registry/core/registry.py

class ToolRegistry:
    def __init__(self, db):
        self.db = db
    
    async def register_tool(self, tool):
        # Implementation for registering a tool
        
    async def get_tool(self, tool_id):
        # Implementation for retrieving a tool
        
    async def list_tools(self):
        # Implementation for listing all tools
        
    async def search_tools(self, query):
        # Implementation for searching tools
        
    async def update_tool(self, tool_id, tool):
        # Implementation for updating a tool
        
    async def delete_tool(self, tool_id):
        # Implementation for deleting a tool
```

### Authentication Service

The authentication service handles user authentication and authorization:

```python
# tool_registry/core/auth.py

class AuthService:
    def __init__(self, db_getter, secret_manager=None):
        self.db_getter = db_getter
        self.secret_manager = secret_manager
        
    async def create_agent(self, agent_create):
        # Implementation for creating an agent
        
    async def get_agent(self, agent_id):
        # Implementation for retrieving an agent
        
    async def authenticate_agent(self, username, password):
        # Implementation for authenticating an agent
        
    async def verify_token(self, token):
        # Implementation for verifying a token
        
    def is_admin(self, agent):
        # Implementation for checking if an agent is an admin
        
    def check_permission(self, agent, permission):
        # Implementation for checking if an agent has a permission
```

### Credential Vendor

The credential vendor generates and manages temporary credentials for tool access:

```python
# tool_registry/core/credentials.py

class CredentialVendor:
    def __init__(self):
        self._credentials = {}
        self._token_to_credential = {}
        
    def generate_credential(self, agent_id, tool_id, duration=None, scopes=None):
        # Implementation for generating a credential
        
    def validate_credential(self, token):
        # Implementation for validating a credential
        
    def revoke_credential(self, credential_id):
        # Implementation for revoking a credential
```

## Extending the Framework

### Adding a New Authentication Method

To add a new authentication method:

1. Create a new authentication class in `tool_registry/auth/`:

```python
# tool_registry/auth/oauth.py

from typing import Optional
from .base import BaseAuth

class OAuthAuth(BaseAuth):
    def __init__(self, config):
        self.config = config
        
    async def authenticate(self, credentials):
        # Implementation for OAuth authentication
        
    async def validate_token(self, token):
        # Implementation for validating an OAuth token
```

2. Register the authentication method in `tool_registry/api/app.py`:

```python
from tool_registry.auth.oauth import OAuthAuth

# Initialize the OAuth authentication
oauth_auth = OAuthAuth(config)
auth_service.register_auth_method("oauth", oauth_auth)
```

### Adding a New Policy Type

To add a new policy type:

1. Create a new policy class in `tool_registry/core/policies/`:

```python
# tool_registry/core/policies/time_based.py

from .base import BasePolicy

class TimeBasedPolicy(BasePolicy):
    def __init__(self, config):
        self.config = config
        
    def evaluate(self, agent, resource, action):
        # Implementation for time-based policy evaluation
        # e.g., only allow access during business hours
```

2. Register the policy in `tool_registry/api/app.py`:

```python
from tool_registry.core.policies.time_based import TimeBasedPolicy

# Initialize the time-based policy
time_policy = TimeBasedPolicy(config)
policy_engine.register_policy("time_based", time_policy)
```

### Adding a New Tool Type

To add a new tool type:

1. Create a new tool class in `tool_registry/core/tools/`:

```python
# tool_registry/core/tools/llm_tool.py

from tool_registry.core.registry import Tool, ToolMetadata

class LLMTool(Tool):
    def __init__(self, name, description, model_name, **kwargs):
        super().__init__(name, description, **kwargs)
        self.model_name = model_name
        
    def execute(self, inputs):
        # Implementation for executing the LLM tool
```

2. Register the tool type in `tool_registry/api/app.py`:

```python
from tool_registry.core.tools.llm_tool import LLMTool

# Register the tool type
tool_registry.register_tool_type("llm", LLMTool)
```

## Testing

The project uses pytest for testing. Tests are located in the `tests/` directory.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tool_registry

# Run specific test files
pytest tests/test_registry.py
pytest tests/test_integration.py
```

### Writing Tests

When writing tests, follow these guidelines:

1. Use fixtures to set up test data and dependencies.
2. Use mocks for external services.
3. Write both unit and integration tests.
4. Use parameterized tests for testing multiple scenarios.
5. Use async tests for asynchronous code.

Example:

```python
# tests/test_registry.py

import pytest
from uuid import UUID
import uuid
import asyncio
from tool_registry.core.registry import Tool, ToolMetadata, ToolRegistry
from tool_registry.core.database import Database, Base

@pytest.fixture
def db():
    # Setup test database
    # ...
    
@pytest.fixture
def tool_metadata():
    # Create sample tool metadata
    # ...
    
@pytest.fixture
def tool(tool_metadata):
    # Create sample tool
    # ...

@pytest.mark.asyncio
async def test_register_tool(db, tool):
    """Test registering a tool."""
    registry = ToolRegistry(db)
    tool_id = await registry.register_tool(tool)
    assert isinstance(tool_id, UUID)
    
    # Verify the tool can be retrieved
    retrieved_tool = await registry.get_tool(tool_id)
    assert retrieved_tool is not None
    assert retrieved_tool.tool_id == tool_id
```

## API Development

The API is built with FastAPI. To add a new endpoint:

1. Create a new endpoint in the appropriate file in `tool_registry/api/`:

```python
# tool_registry/api/endpoints/tool_usage.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from tool_registry.core.registry import ToolUsage
from tool_registry.auth import get_current_agent

router = APIRouter()

@router.get("/tools/{tool_id}/usage", response_model=List[ToolUsage])
async def get_tool_usage(tool_id: UUID, current_agent = Depends(get_current_agent)):
    """Get usage statistics for a tool."""
    # Implementation for getting tool usage statistics
```

2. Include the router in `tool_registry/api/app.py`:

```python
from tool_registry.api.endpoints import tool_usage

app.include_router(tool_usage.router, tags=["tools"])
```

## Customizing Monitoring and Logging

The monitoring system can be customized to integrate with different logging and metrics systems:

```python
# tool_registry/core/monitoring.py

from prometheus_client import Counter, Histogram, start_http_server

class CustomMonitoring:
    def __init__(self, config):
        self.config = config
        
    def setup(self):
        # Setup custom monitoring
        
    def record_request(self, method, endpoint, status_code, duration):
        # Record a request
        
    def record_error(self, method, endpoint, error):
        # Record an error
```

## Deployment Considerations

### Scaling

The GenAI Tool Registry can be scaled in several ways:

1. **Horizontal Scaling**: Run multiple instances behind a load balancer.
2. **Database Scaling**: Use a scalable database like PostgreSQL with proper indexing.
3. **Caching**: Implement caching for frequently accessed data.

### Security

Consider these security measures for production:

1. **HTTPS**: Always use HTTPS in production.
2. **JWT Secret**: Use a strong, randomly generated JWT secret.
3. **Rate Limiting**: Enable rate limiting to prevent abuse.
4. **Firewall**: Configure a firewall to restrict access to the API.
5. **Authentication**: Use strong authentication methods.

### Monitoring

Monitor the system using the built-in Prometheus metrics:

1. **Request Metrics**: Track request volume, latency, and error rates.
2. **Resource Metrics**: Monitor CPU, memory, and disk usage.
3. **Database Metrics**: Monitor database connections and query performance.

## Contributing Guidelines

When contributing to the project:

1. **Code Style**: Follow PEP 8 and use black for code formatting.
2. **Documentation**: Update the documentation when making changes.
3. **Tests**: Write tests for new functionality and ensure existing tests pass.
4. **Pull Requests**: Make small, focused pull requests with clear descriptions.
5. **Commit Messages**: Write clear commit messages explaining the changes.

## Troubleshooting

Common issues and their solutions:

1. **Database Connection Issues**: Check the database connection string and ensure the database server is running.
2. **Authentication Failures**: Verify the JWT secret key is correctly set and that tokens are valid.
3. **Rate Limiting Issues**: Check the Redis connection if rate limiting is enabled.
4. **Performance Problems**: Look for slow database queries or missing indexes.

## Community and Support

Connect with the community:

- GitHub Issues: Report bugs and suggest features
- Discussions: Ask questions and share ideas
- Contributing: Read the contributing guidelines to get started 