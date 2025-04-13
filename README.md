# Tool Registry

Tool Registry is a comprehensive system for managing, securing, and controlling access to AI tools and services. It enables organizations to track, govern, and monitor tool usage in AI applications.

## Features

- **Tool Management**: Register, update, and delete tools with detailed metadata
- **Access Control**: Fine-grained policy-based access control for tools
- **Agent Identity**: Manage identities for agents (users, services, bots) accessing tools
- **Credential Management**: Secure credential issuance and validation
- **Usage Tracking**: Monitor and analyze tool usage patterns
- **Rate Limiting**: Set and enforce usage limits per agent or policy
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
   alembic upgrade head
   ```

6. Start the server
   ```
   uvicorn tool_registry.main:app --reload
   ```

The API will be available at http://localhost:8000.

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

- [API Reference](docs/api_reference.md)
- [Architecture Overview](docs/architecture.md)
- [Schema Reference](docs/schema_reference.md)
- [Security Model](docs/security.md)
- [Deployment Guide](docs/deployment.md)

## Development

### Running Tests

```
python -m pytest -v
```

With coverage report:

```
python -m pytest --cov=tool_registry tests/
```

### Code Style

We use Black for code formatting and isort for import sorting:

```
black tool_registry tests
isort tool_registry tests
```

### Environment Variables

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT token generation
- `DEBUG`: Enable debug mode (True/False)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `ALLOWED_ORIGINS`: CORS allowed origins, comma-separated

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Format your code (`black .` and `isort .`)
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Project Team - your.email@example.com

Project Link: [https://github.com/yourusername/tool-registry](https://github.com/yourusername/tool-registry) 