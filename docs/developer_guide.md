# GenAI Tool Registry Developer Guide

## Project Structure

The Tool Registry is organized into the following directories:

```
tool-registry/
├── tool_registry/           # Main package
│   ├── __init__.py
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── core/                # Core functionality
│   ├── api/                 # API endpoints
│   ├── auth/                # Authentication
│   ├── services/            # Business logic
│   └── utils/               # Utility functions
├── tests/                   # Tests
├── docs/                    # Documentation
├── migrations/              # Database migrations
└── README.md                # README file
```

## Design Principles

The Tool Registry is designed with the following principles in mind:

1. **Modularity**: Each component has a single responsibility.
2. **Type Safety**: All interfaces are typed with Python type hints.
3. **Security**: Authentication and authorization are built-in.
4. **Extensibility**: The system can be extended with new features.
5. **Documentation**: All components are well-documented.

## Core Components

### Registry Service

The Registry Service (`tool_registry/core/registry.py`) is responsible for managing tools. It provides methods for registering, retrieving, updating, deleting, and searching tools.

```python
class ToolRegistry:
    def __init__(self, db: Database):
        self.db = db
    
    async def register_tool(self, tool_data: ToolCreate, owner_id: UUID) -> Tool:
        # Implementation
        
    async def get_tool(self, tool_id: UUID) -> Optional[Tool]:
        # Implementation
        
    async def search_tools(self, query: str) -> List[Tool]:
        # Implementation
```

### Authentication Service

The Authentication Service (`tool_registry/auth/authentication.py`) is responsible for authenticating API calls. It provides methods for validating credentials and generating API keys.

### Authorization Service

The Authorization Service (`tool_registry/auth/authorization.py`) is responsible for authorizing access to tools. It provides methods for creating and evaluating policies.

## Logging System

The Tool Registry implements a comprehensive logging system to provide insight into the application's behavior, particularly for critical security components.

### Credential Vendor Logging

The `CredentialVendor` class (`tool_registry/credential_vendor.py`) includes detailed logging for all credential operations:

- **Initialization**: Logs when the vendor is initialized
- **Generation**: Logs when credentials are generated, including details about the agent, tool, and scope
- **Validation**: Logs validation attempts, token details, and validation results
- **Revocation**: Logs when credentials are revoked
- **Cleanup**: Logs expired credential cleanup activities

Example of using the logs for debugging credential issues:

```python
# Set logging level to DEBUG to see all credential operations
import logging
logging.getLogger('tool_registry.credential_vendor').setLevel(logging.DEBUG)
```

### Rate Limiter Logging

The `RateLimiter` class (`tool_registry/core/rate_limit.py`) includes detailed logging for rate limiting operations:

- **Initialization**: Logs when the rate limiter is initialized with configuration details
- **Request Checking**: Logs when a request is checked against the rate limit
- **Redis Operations**: Logs Redis interactions for distributed rate limiting
- **Fallback Operations**: Logs when the system falls back to in-memory storage
- **Rate Limit Decisions**: Logs detailed information about rate limit decisions

Example logs to look for when troubleshooting rate limiting issues:

```
INFO:tool_registry.core.rate_limit:RateLimiter initialized with limit: 100/60s, Redis: Enabled
DEBUG:tool_registry.core.rate_limit:Checking rate limit for 192.168.1.1 at 2023-06-20T12:34:56
DEBUG:tool_registry.core.rate_limit:Request allowed for 192.168.1.1, remaining: 99/100, reset window: 60s
WARNING:tool_registry.core.rate_limit:Rate limit exceeded for 192.168.1.1: 100/100 at 2023-06-20T12:35:30
```

### Best Practices for Logging

1. **Log Levels**: Use appropriate log levels:
   - `DEBUG`: Detailed information for debugging
   - `INFO`: General information about system operation
   - `WARNING`: Unusual events that don't affect normal operation
   - `ERROR`: Errors that prevent proper functioning

2. **Context Information**: Include relevant context in log messages, such as:
   - Identifiers (agent_id, tool_id, credential_id)
   - Timestamps
   - Operation results
   - Error details

3. **Performance Considerations**: 
   - Use conditional logging for expensive operations
   - Keep high-volume DEBUG logs behind level checks
   - Consider structured logging for production environments

## Database Schema

The Tool Registry uses SQLAlchemy as its ORM. A complete database schema is documented in `docs/schema.md`.

### Key Models

- **Tool**: Represents a registered AI tool
- **ToolMetadata**: Contains additional metadata about a tool
- **Agent**: Represents a user or service that interacts with tools
- **Policy**: Defines access control rules for tools
- **Credential**: Stores authentication credentials
- **AccessLog**: Records access attempts

## SQLAlchemy Model Relationships

Models are related through foreign keys and SQLAlchemy relationships. Here are the key relationships:

- An **Agent** can own multiple **Tools**
- A **Tool** has one **ToolMetadata** record
- A **Tool** can have multiple **Policies**
- An **Agent** can have multiple **Credentials**
- Access attempts are recorded in **AccessLog**

## Common SQLAlchemy Issues and Best Practices

### Avoiding Reserved Attribute Names

SQLAlchemy reserves certain attribute names that should not be used in models:

```python
# Incorrect
class Tool(Base):
    metadata = relationship("ToolMetadata", back_populates="tool")  # Conflicts with SQLAlchemy's metadata

# Correct
class Tool(Base):
    tool_metadata_rel = relationship("ToolMetadata", back_populates="tool")
```

### Proper Session Management

Always use context managers or try/finally blocks when working with database sessions:

```python
# Best practice
async def get_tool(self, tool_id: UUID) -> Optional[Tool]:
    session = next(self.db.get_session())
    try:
        tool = session.query(Tool).filter(Tool.tool_id == tool_id).first()
        return tool
    finally:
        session.close()
```

### Default Values for JSON Columns

Always provide default values for JSON columns:

```python
# Correct
auth_config = Column(JSON, nullable=False, default=dict)
tags = Column(JSON, nullable=False, default=list)
```

### Circular Import Issues

To avoid circular imports, use strings for relationship target classes:

```python
# Correct
tool = relationship("Tool", back_populates="policies")
```

## API Design

The API follows RESTful principles and is defined using FastAPI. Each endpoint is documented with OpenAPI specs.

### Endpoint Structure

- `/tools`: Tool management
- `/agents`: Agent management
- `/policies`: Policy management
- `/auth`: Authentication endpoints

## Error Handling

All errors are returned as JSON responses with appropriate HTTP status codes. The error response format is:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2023-05-01T12:00:00Z"
}
```

## Testing

The codebase uses pytest for testing. Tests are organized by component:

- Unit tests: Test individual functions
- Integration tests: Test interactions between components
- API tests: Test API endpoints

To run tests, use:

```bash
python -m pytest
```

## Debugging

For debugging, you can enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development Workflow

1. Create a feature branch from `main`
2. Implement your changes
3. Add tests
4. Run tests locally
5. Submit a pull request

## Environment Variables

The application uses the following environment variables:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT signing
- `DEBUG`: Enable debug mode (true/false)
- `TEST_MODE`: Enable test mode (true/false)

## Development Setup

1. Clone the repository
2. Install dependencies: `pip install -e ".[dev]"`
3. Set up environment variables
4. Run migrations: `alembic upgrade head`
5. Start the server: `python -m tool_registry`

## Tool Registration Example

```python
from tool_registry.core.registry import ToolRegistry
from tool_registry.schemas.tool import ToolCreate
from tool_registry.db.database import Database
import uuid

db = Database(database_url="sqlite:///tool_registry.db")
registry = ToolRegistry(db)

# Create a tool
tool_data = ToolCreate(
    name="TextSummary",
    description="Summarizes text documents",
    api_endpoint="https://api.example.com/summarize",
    auth_method="api_key",
    auth_config={"header_name": "X-API-Key"},
    params={"text": {"type": "string", "required": True}},
    version="1.0.0",
    tags=["text", "summarization"]
)

# Register the tool
owner_id = uuid.uuid4()  # Replace with actual owner ID
tool = await registry.register_tool(tool_data, owner_id)
print(f"Tool registered with ID: {tool.tool_id}")
```

## Using the Authorization Service

```python
from tool_registry.auth.authorization import AuthorizationService
from tool_registry.db.database import Database
import uuid

db = Database(database_url="sqlite:///tool_registry.db")
auth_service = AuthorizationService(db)

# Create a policy
policy_data = {
    "name": "BasicAccess",
    "description": "Basic access policy for the TextSummary tool",
    "tool_id": uuid.UUID("your-tool-id"),
    "allowed_scopes": ["read"],
    "conditions": {"ip_range": ["192.168.1.0/24"]},
    "rules": {"rate_limit": 100}
}

policy = await auth_service.create_policy(policy_data)
print(f"Policy created with ID: {policy.policy_id}")

# Check access
agent_id = uuid.UUID("your-agent-id")
tool_id = uuid.UUID("your-tool-id")
scope = "read"
is_allowed = await auth_service.check_access(agent_id, tool_id, scope)
print(f"Access allowed: {is_allowed}")
```

## Troubleshooting

### Common Issues

1. **SQLAlchemy metadata conflict**: Rename any model attributes named `metadata` to avoid conflicts.
2. **JSON column type errors**: Ensure default values are provided for JSON columns.
3. **Circular import errors**: Use string references in relationships.
4. **Database connection issues**: Check your DATABASE_URL environment variable.

### Debugging Database Issues

To debug database issues, enable SQLAlchemy echo:

```python
engine = create_engine(database_url, echo=True)
```

## Contributing

See the [Contributing Guide](CONTRIBUTING.md) for information on how to contribute to the project.

## Additional Resources

- [Schema Documentation](schema.md)
- [API Reference](api_reference.md)
- [Installation Guide](installation.md) 