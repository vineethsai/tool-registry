# GenAI Tool Registry

An open-source framework for managing GenAI tool access with secure authentication, authorization, and just-in-time credential vending.

## Features

- **Secure Tool Registry**: Register, discover, and manage tools with detailed metadata
- **Authentication & Authorization**: Role-based access control and permission management
- **Just-in-Time Credentials**: Temporary, scoped credentials for tool access
- **Extensible Architecture**: Easy to extend with new authentication methods and policies
- **RESTful API**: FastAPI-based API for easy integration
- **Type Safety**: Built with Pydantic for robust data validation
- **Secret Management**: Integration with HashiCorp Vault for secure secret storage
- **Structured Logging**: Comprehensive logging and monitoring with Prometheus metrics
- **Rate Limiting**: Configurable rate limiting to protect resources
- **Database Integration**: SQLAlchemy ORM with support for multiple database backends

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (optional, SQLite can be used for development)
- Redis (optional, for rate limiting)
- HashiCorp Vault (optional, for secret management)

### Standard Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tool-registry.git
cd tool-registry
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Development Installation

If you plan to contribute to the project or run tests:

```bash
pip install -r requirements-test.txt
pip install -e .
```

### Environment Configuration

Create a `.env` file in the root directory with the following variables:

```
DATABASE_URL=sqlite:///./tool_registry.db  # or postgresql://user:password@localhost/tool_registry
REDIS_URL=redis://localhost:6379/0  # optional
JWT_SECRET_KEY=your-secret-key
VAULT_URL=http://localhost:8200  # optional
VAULT_TOKEN=your-vault-token  # optional
LOG_LEVEL=INFO
```

## Quick Start

1. Start the API server:
```bash
uvicorn tool_registry.api.app:app --reload
```

2. Access the API documentation at `http://localhost:8000/docs`

3. Try the example:
```bash
python -m tool_registry.examples.example
```

## Testing

The project includes comprehensive tests for all components:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tool_registry

# Run specific test files
pytest tests/test_registry.py
pytest tests/test_integration.py
```

## Architecture

The GenAI Tool Registry is built using a modular architecture:

### Core Components

1. **Registry Module** (`tool_registry.core.registry`):
   - Manages tool registration, listing, searching, and retrieval
   - Handles tool metadata and versioning

2. **Authentication Module** (`tool_registry.core.auth`):
   - JWT-based authentication
   - Agent management (users, services, etc.)
   - Role-based access control

3. **Credential Vending** (`tool_registry.core.credentials`):
   - Just-in-time credential generation
   - Scoped access tokens
   - Automatic credential expiration

4. **Database Layer** (`tool_registry.core.database`):
   - SQLAlchemy ORM
   - Model definitions
   - Database migrations

5. **Configuration** (`tool_registry.core.config`):
   - Environment-based configuration
   - Integration with HashiCorp Vault for secrets

6. **Monitoring** (`tool_registry.core.monitoring`):
   - Structured logging
   - Prometheus metrics
   - Request tracing

7. **Rate Limiting** (`tool_registry.core.rate_limit`):
   - Request rate limiting
   - Redis-based counter implementation
   - Configurable time windows and limits

### API Layer

The API is built with FastAPI and provides the following endpoints:

### Authentication
- `POST /token`: Get authentication token
- `POST /agents`: Create a new agent

### Tools
- `POST /tools/`: Register a new tool
- `GET /tools`: List all tools
- `GET /tools/search`: Search tools
- `GET /tools/{tool_id}`: Get tool details
- `PUT /tools/{tool_id}`: Update a tool
- `DELETE /tools/{tool_id}`: Delete a tool
- `POST /tools/{tool_id}/access`: Request tool access

## Tool Model

A tool in the registry is defined by the following properties:

```python
{
    "tool_id": "unique-uuid",
    "name": "Example Tool",
    "description": "Tool description",
    "version": "1.0.0",
    "tool_metadata_rel": {
        "schema_version": "1.0",
        "inputs": {
            "text": {"type": "string"}
        },
        "outputs": {
            "result": {"type": "string"}
        }
    },
    "endpoint": "/api/tools/example",
    "auth_required": true,
    "auth_type": "api_key",  # optional
    "auth_config": {},  # optional
    "rate_limit": 100,  # optional
    "cost_per_call": 0.01  # optional
}
```

## Usage Examples

### Registering a Tool

```python
from tool_registry.core.registry import Tool, ToolMetadata
from tool_registry.core.database import Database

# Initialize database
db = Database("sqlite:///./tool_registry.db")
db.init_db()

# Create a tool with metadata
tool = Tool(
    name="Example Tool",
    description="An example tool for demonstration",
    version="1.0.0",
    tool_metadata_rel=ToolMetadata(
        schema_version="1.0",
        inputs={"text": {"type": "string"}},
        outputs={"result": {"type": "string"}}
    ),
    endpoint="https://api.example.com/tool",
    auth_required=True
)

# Register the tool
registry = ToolRegistry(db)
tool_id = await registry.register_tool(tool)
print(f"Tool registered with ID: {tool_id}")
```

### Using the API

```python
import requests

# Get an authentication token
response = requests.post(
    "http://localhost:8000/token",
    data={"username": "admin", "password": "password"}
)
token = response.json()["access_token"]

# Register a tool
tool_data = {
    "name": "Test Tool",
    "description": "A test tool",
    "version": "1.0.0",
    "tool_metadata": {
        "schema_version": "1.0",
        "inputs": {"text": {"type": "string"}},
        "outputs": {"result": {"type": "string"}}
    }
}

response = requests.post(
    "http://localhost:8000/tools/",
    json=tool_data,
    headers={"Authorization": f"Bearer {token}"}
)
tool = response.json()
print(f"Tool registered: {tool['tool_id']}")
```

## Security Considerations

- All API endpoints require authentication
- Credentials are short-lived and scoped to specific tools
- Role-based access control
- Permission-based authorization
- Rate limiting support
- Cost tracking per tool call
- Secrets stored securely in HashiCorp Vault
- HTTPS recommended for production deployments

## Extending the Framework

### Adding New Authentication Methods
1. Create a new authentication class
2. Implement the required methods
3. Register with the AuthService

### Adding New Policy Types
1. Create a new policy class
2. Implement policy evaluation logic
3. Register with the PolicyEngine

### Adding New Credential Types
1. Create a new credential class
2. Implement credential generation and validation
3. Register with the CredentialVendor

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure your code passes all tests and follows the project's coding style.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 