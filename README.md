# Tool Registry

Tool Registry is a comprehensive system for managing, securing, and controlling access to AI tools and services. It enables organizations to track, govern, and monitor tool usage in AI applications.

> **IMPORTANT WARNING: AUTHENTICATION IS DISABLED**  
> Authentication has been temporarily disabled to facilitate development and testing. The API is currently accessible without credentials. Before deploying to production, authentication MUST be re-enabled. Refer to the authentication setup in the code and configuration.

## Features

- **Tool Management**: Register, update, and delete tools with detailed metadata
- **Access Control**: Fine-grained policy-based access control for tools
- **Agent Identity**: Manage identities for agents (users, services, bots) accessing tools
- **Credential Management**: Secure credential issuance and validation
- **Usage Tracking**: Monitor and analyze tool usage patterns
- **Rate Limiting**: Set and enforce usage limits per agent or policy
- **Enhanced Logging**: Comprehensive logging for rate limiting and credential operations
- **API Integration**: RESTful API for seamless integration

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL or SQLite database
- pip (Python package manager)

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/tool-registry.git
   cd tool-registry
   ```

2. Create and activate a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Configure the database
   ```
   # For SQLite (development)
   export DATABASE_URL="sqlite:///tool_registry.db"
   
   # For PostgreSQL (production)
   export DATABASE_URL="postgresql://user:password@localhost/tool_registry"
   ```

5. Run database migrations
   ```
   # Alembic setup might be missing, this step might not apply directly.
   # Database tables are created on startup via start.sh
   # If using Alembic, uncomment and ensure it's configured:
   # alembic upgrade head
   ```

6. Start the server
   ```
   # Using the provided start script (handles DB init)
   ./start.sh
   
   # Or directly with uvicorn (if DB is already initialized)
   # uvicorn tool_registry.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

The API will be available at http://localhost:8000.

### Using the Postman Collection

The project includes a comprehensive Postman collection for testing the API:

1. Install [Postman](https://www.postman.com/downloads/)
2. Import the collection from `postman/tool_registry_api_collection.json`
3. Import the environment from `postman/tool_registry_environment.json`
4. Select the "Tool Registry API Environment" from the environment dropdown

To serve the Postman documentation locally, you can use the provided script (requires Python 3):
```
./serve_postman_docs.sh
```

This will attempt to start the server on port 8080 or another available port.

When running with Docker Compose, the Postman documentation is available at http://localhost:9000/tool_registry_api_collection.json.

See [Postman Documentation](postman/README.md) for more details on using the collection.

## Usage Examples

### Register a Tool

```python
import requests
import json

token = "your_auth_token"
api_url = "http://localhost:8000/api/v1"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

tool_data = {
    "name": "Image Generator",
    "description": "AI tool for generating images from text prompts",
    "api_endpoint": "https://api.example.com/generate",
    "auth_method": "oauth2",
    "auth_config": {
        "token_url": "https://api.example.com/oauth/token",
        "client_id": "${CLIENT_ID}",
        "scope": "image:generate"
    },
    "params": {
        "prompt": {"type": "string", "required": True},
        "style": {"type": "string", "required": False, "default": "realistic"}
    },
    "version": "1.0.0",
    "tags": ["image", "generation", "ai"]
}

response = requests.post(
    f"{api_url}/tools",
    headers=headers,
    data=json.dumps(tool_data)
)

print(response.json())
```

For more examples, see [Usage Examples](docs/usage_examples.md).

## Documentation

- API Reference: Available via Swagger UI (`/docs`) and ReDoc (`/redoc`) when the server is running.
- [Architecture Overview](docs/architecture.md) (Needs review/creation)
- [Schema Reference](docs/schema_reference.md) (Needs review/creation)
- [Security Model](docs/security.md) (Needs review/creation)
- [Deployment Guide](docs/deployment_guide.md)
- [Docker Guide](DOCKER.md)
- [Postman Collection Guide](postman/README.md)

## Development

### Running Tests

```
pytest
```

With coverage report:

```
pytest --cov=tool_registry --cov-report=html
# Open coverage_html_report/index.html in your browser
```

### Code Style

We use Black for code formatting and isort for import sorting:

```
black tool_registry tests
isort tool_registry tests
```

### Environment Variables

- `DATABASE_URL`: Database connection string
- `SECRET_KEY` / `JWT_SECRET_KEY`: Secret key for JWT token generation (check `tool_registry/core/config.py` for exact name)
- `DEBUG`: Not explicitly used, `LOG_LEVEL` controls verbosity.
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `ALLOWED_ORIGINS`: CORS allowed origins (Handled by FastAPI middleware, check `tool_registry/api/app.py`)
- `VAULT_URL`, `VAULT_TOKEN`: Optional Vault configuration
- `REDIS_URL`: Required for rate limiting

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Format your code (`black .` and `isort .`)
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Vineeth Sai Narajala

Project Link: [https://github.com/yourusername/tool-registry](https://github.com/yourusername/tool-registry) (Please update this link) 