# GenAI Tool Registry

An open-source framework for managing GenAI tool access with secure authentication, authorization, and just-in-time credential vending.

## Key Security Features

- **Role-Based Access Control**: Tools are only accessible by authorized agents based on their roles and permissions
- **Just-in-Time Credentials**: Temporary, scoped credentials for specific tasks to enhance security
- **Policy Engine**: Robust policy engine to enforce access rules based on multiple conditions
- **Scoped Access**: Fine-grained permission control with specific scopes (read, write, etc.)
- **Comprehensive Logging**: Audit trail of all access attempts and credential usage
- **Token-Based Authentication**: Secure JWT tokens for both agent authentication and tool credentials

## Architecture

The GenAI Tool Registry is built using a modular architecture:

### Core Components

1. **Registry Module**: 
   - Manages tool registration, discovery, and metadata
   - Handles versioning and tool lifecycle

2. **Authentication Module**:
   - Agent authentication and identity management
   - Token generation and validation
   - Role assignment and management

3. **Authorization Module**:
   - Policy-based access control
   - Context-aware authorization decisions
   - Custom rule evaluation

4. **Credential Vendor**:
   - Just-in-time credential generation
   - Scoped access tokens
   - Credential lifecycle management

5. **Monitoring & Logging**:
   - Access attempt logging
   - Credential usage tracking
   - Audit trail for compliance

## Security Flow

1. **Agent Authentication**:
   - Agent provides credentials
   - System verifies identity and issues a session token
   - Agent roles and permissions are loaded

2. **Tool Discovery**:
   - Agent browses or searches for available tools
   - Only tools that the agent potentially has access to are displayed

3. **Access Request**:
   - Agent requests access to a specific tool with desired scopes
   - Policy engine evaluates request against defined policies
   - Context (time, location, previous usage) is considered

4. **Credential Issuance**:
   - If access is granted, a temporary credential is issued
   - Credential has limited scope and expiration time
   - Usage is tracked for audit purposes

5. **Tool Access**:
   - Agent uses the temporary credential to access the tool
   - Tool validates the credential on each request
   - Actions are limited to granted scopes

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
- HashiCorp Vault (optional, for enhanced secret management)

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
JWT_SECRET_KEY=your-secret-key-here
CREDENTIAL_JWT_SECRET=your-credential-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
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

## API Usage

### Authentication

```python
import requests

# Get an authentication token
response = requests.post(
    "http://localhost:8000/token",
    data={"username": "agent1", "password": "password"}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
```

### Tool Registration

```python
# Register a new tool
tool_data = {
    "name": "Text Translation API",
    "description": "Translates text between languages",
    "api_endpoint": "https://api.example.com/translate",
    "auth_method": "API_KEY",
    "auth_config": {
        "header_name": "X-API-Key"
    },
    "params": {
        "source_language": {"type": "string", "required": True},
        "target_language": {"type": "string", "required": True},
        "text": {"type": "string", "required": True}
    },
    "tags": ["translation", "text", "language"],
    "version": "1.0.0"
}

response = requests.post(
    "http://localhost:8000/tools",
    json=tool_data,
    headers=headers
)
tool = response.json()
```

### Tool Access

```python
# Request access to a tool
response = requests.post(
    f"http://localhost:8000/tools/{tool['tool_id']}/access",
    params={"scopes": ["read", "translate"]},
    headers=headers
)
access_info = response.json()
credential = access_info["credential"]

# Use the credential to access the tool
tool_response = requests.post(
    tool["api_endpoint"],
    headers={"Authorization": f"Bearer {credential['token']}"},
    json={
        "source_language": "en",
        "target_language": "es",
        "text": "Hello world"
    }
)
```

## Policy Examples

### Role-Based Policy

```python
policy = {
    "name": "Translator Access",
    "description": "Allows translators to access translation tools",
    "rules": {
        "roles": ["translator", "admin"],
        "allowed_scopes": ["read", "translate"],
        "max_credential_lifetime": 3600  # 1 hour
    }
}
```

### Time-Based Policy

```python
policy = {
    "name": "Business Hours Only",
    "description": "Restricts access to business hours",
    "rules": {
        "time_restrictions": {
            "allowed_days": [0, 1, 2, 3, 4],  # Monday to Friday
            "allowed_hours": [(9, 17)]  # 9 AM to 5 PM
        }
    }
}
```

### Resource Limit Policy

```python
policy = {
    "name": "API Usage Limits",
    "description": "Limits API usage to prevent abuse",
    "rules": {
        "resource_limits": {
            "max_calls_per_minute": 100,
            "max_cost_per_day": 10.0
        }
    }
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 