# Troubleshooting Guide for Tool Registry

This document provides solutions for common issues you may encounter when working with the GenAI Tool Registry.

## Database Connection Issues

### Issue: Unable to Connect to Database

**Symptoms:**
- Error message: `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file`
- Application fails to start with database connection errors

**Solutions:**
1. Check database file path:
   ```python
   # For SQLite
   db = Database("sqlite:///./tool_registry.db")  # Note the three slashes for relative path
   ```

2. Verify database file permissions:
   ```bash
   # Check permissions
   ls -la tool_registry.db
   
   # Set proper permissions if needed
   chmod 644 tool_registry.db
   ```

3. For PostgreSQL or MySQL, verify connection parameters:
   ```python
   # Correct format
   db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
   db = Database(db_url)
   ```

### Issue: Migration Errors

**Symptoms:**
- Error message: `alembic.util.exc.CommandError: Can't locate revision identified by '...'`
- Tables not being created correctly

**Solutions:**
1. Reset migrations (in development only):
   ```bash
   # Remove existing migration data
   rm -rf alembic/versions/*
   rm -f alembic/alembic.ini
   
   # Reinitialize migrations
   alembic init alembic
   alembic revision --autogenerate -m "initial"
   alembic upgrade head
   ```

2. Fix specific migration:
   ```bash
   # Create a new migration to fix issues
   alembic revision --autogenerate -m "fix_table_issues"
   ```

## SQLAlchemy Model Errors

### Issue: Reserved Attribute Name 'metadata'

**Symptoms:**
- Error message: `sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved`

**Solution:**
Rename any attribute or relationship named 'metadata' in your models:

```python
# Instead of this
class Tool(Base):
    # ...
    metadata = relationship("ToolMetadata", back_populates="tool")

# Use this
class Tool(Base):
    # ...
    tool_metadata_rel = relationship("ToolMetadata", back_populates="tool")
```

### Issue: Relationship ConfigurationError

**Symptoms:**
- Error message: `sqlalchemy.exc.ArgumentError: relationship 'Tool.policies' expects a class or mapper argument`

**Solution:**
Ensure all related models are imported and defined before references:

```python
# At the top of your models file
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime, JSON

# Define all models, then set up relationships with proper references
```

### Issue: UUID Serialization Issues

**Symptoms:**
- Error messages about UUID serialization when using SQLite

**Solution:**
Add a UUID type handler for SQLite:

```python
from sqlalchemy.types import TypeDecorator, VARCHAR
import uuid

class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = VARCHAR
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value
```

## API Errors

### Issue: 422 Validation Error

**Symptoms:**
- API returns 422 status code with validation error details

**Solution:**
Check the request payload against the expected schema:

```python
# Example of correct tool creation payload
tool_data = {
    "name": "My Tool",
    "description": "Tool description",
    "api_endpoint": "https://api.example.com",
    "auth_method": "api_key",  # Must be one of the valid methods
    "params": {},  # Must match expected schema
    "version": "1.0.0"  # Must be valid semver format
}
```

### Issue: 401 Unauthorized

**Symptoms:**
- API returns 401 status code
- Unable to access protected endpoints

**Solutions:**
1. Check authentication token:
   ```python
   # Ensure you're passing the token correctly
   headers = {"Authorization": f"Bearer {token}"}
   ```

2. Verify token expiration:
   ```python
   # Get a fresh token
   auth_response = requests.post("/auth/token", data={"username": "user", "password": "pass"})
   ```

### Issue: 403 Forbidden

**Symptoms:**
- API returns 403 status code
- Unable to perform certain actions

**Solution:**
Check user permissions and policies:

```python
# Check if policy exists for this tool and agent
from tool_registry.core.authorization import AuthorizationService
auth_service = AuthorizationService(db)
policies = auth_service.get_policies_for_tool(tool_id)

# Create policy if needed
if not policies:
    policy_data = PolicyCreate(
        name="Default Access",
        tool_id=tool_id,
        allowed_scopes=["read", "execute"]
    )
    auth_service.create_policy(policy_data)
```

## Runtime Errors

### Issue: Tool Execution Failure

**Symptoms:**
- Error messages when attempting to execute a tool
- API returns 500 status code

**Solutions:**
1. Check tool configuration:
   ```python
   # Get tool details
   tool = registry.get_tool(tool_id)
   print(f"API Endpoint: {tool.api_endpoint}")
   print(f"Auth Method: {tool.auth_method}")
   ```

2. Verify credentials:
   ```python
   # Check if credentials exist and are valid
   from tool_registry.core.credential import CredentialManager
   cred_manager = CredentialManager(db)
   credentials = cred_manager.get_credential(tool_id=tool_id, agent_id=agent_id)
   
   if not credentials or credentials.expires_at < datetime.now():
       print("Credentials are missing or expired")
   ```

3. Test the API endpoint directly:
   ```bash
   # Using curl to test the endpoint
   curl -X POST "https://api.example.com/endpoint" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"param": "value"}'
   ```

### Issue: Rate Limiting Problems

**Symptoms:**
- Errors about exceeding rate limits
- Inconsistent access to tools

**Solution:**
Check rate limit configuration and current usage:

```python
from tool_registry.core.rate_limiter import RateLimiter

# Check current usage
rate_limiter = RateLimiter(db)
current_usage = rate_limiter.get_current_usage(agent_id, tool_id)
print(f"Current usage: {current_usage} requests")

# Update rate limit if needed
from tool_registry.schemas.policy import PolicyUpdate
auth_service.update_policy(
    policy_id=policy_id,
    policy_data=PolicyUpdate(
        rules={"rate_limit": {"requests": 200, "period": "hour"}}
    )
)
```

## Testing Issues

### Issue: Test Database Setup

**Symptoms:**
- Tests fail with database errors
- Inconsistent test results

**Solutions:**
1. Use in-memory database for tests:
   ```python
   @pytest.fixture
   def db():
       # Use in-memory SQLite for tests
       db = Database("sqlite:///:memory:")
       db.init_db()
       yield db
   ```

2. Ensure database cleanup after tests:
   ```python
   @pytest.fixture(autouse=True)
   def cleanup_db(db):
       yield
       # Drop all tables after test
       Base.metadata.drop_all(bind=db.engine)
   ```

### Issue: Mock Authentication in Tests

**Symptoms:**
- Authentication failures during tests
- Unable to test protected endpoints

**Solution:**
Create a test authentication helper:

```python
@pytest.fixture
def auth_headers():
    # Create mock JWT token for testing
    from tool_registry.auth.jwt import create_access_token
    
    # Create test user
    test_user = {"sub": "test_user", "scopes": ["admin"]}
    token = create_access_token(test_user)
    
    return {"Authorization": f"Bearer {token}"}

# Use in tests
def test_protected_endpoint(client, auth_headers):
    response = client.get("/protected/endpoint", headers=auth_headers)
    assert response.status_code == 200
```

## Common Code Issues

### Issue: Missing Required Fields

**Symptoms:**
- Validation errors when creating objects
- 422 errors from API

**Solution:**
Check that all required fields are included:

```python
# Make sure all required fields are provided
tool_data = ToolCreate(
    name="Tool Name",  # Required
    description="Description",  # Required
    api_endpoint="https://api.example.com",  # Required
    auth_method="api_key",  # Required
    # Other fields...
)
```

### Issue: Incorrect Data Types

**Symptoms:**
- Type errors when passing data between layers
- Serialization errors

**Solution:**
Double-check data types match schema expectations:

```python
# Ensure UUIDs are properly formatted
from uuid import UUID

# Correct
tool_id = UUID("550e8400-e29b-41d4-a716-446655440000")

# Incorrect - will cause errors
tool_id = "550e8400-e29b-41d4-a716-446655440000"  # Should be UUID type
```

## Debugging Tools

### Enable Detailed Logging

```python
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='tool_registry_debug.log'
)

# Get logger in your modules
logger = logging.getLogger(__name__)
logger.debug("Detailed information for debugging")
```

### Database Query Logging

```python
# Enable SQLAlchemy query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### API Request/Response Logging

For FastAPI applications:

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response
```

## Getting Additional Help

If you continue to experience issues after trying the solutions in this guide:

1. Check the GitHub repository issues: [Tool Registry Issues](https://github.com/yourorg/tool-registry/issues)
2. Review the latest documentation
3. Capture detailed logs and error messages
4. Create a new issue with:
   - Description of the problem
   - Steps to reproduce
   - Error messages and logs
   - Version information (Python, SQLAlchemy, FastAPI, etc.)

## Common Environment Setup Issues

### Python Version Compatibility

**Issue:** Errors related to syntax or missing features

**Solution:** Ensure you're using Python 3.9 or higher:

```bash
# Check Python version
python --version

# If needed, install or switch to a compatible version
pyenv install 3.9.6
pyenv local 3.9.6
```

### Virtual Environment Problems

**Issue:** Package conflicts or import errors

**Solution:** Create a clean virtual environment:

```bash
# Remove existing venv if problematic
rm -rf venv

# Create fresh environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
``` 