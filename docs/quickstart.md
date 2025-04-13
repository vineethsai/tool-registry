# Tool Registry Quick Start Guide

> **IMPORTANT NOTE**: Authentication is currently disabled for development purposes. API endpoints can be accessed without authentication tokens. The credential management system remains in place but is not enforced.

This guide will help you quickly set up and start using the Tool Registry API.

## Setup

### Prerequisites

- Python 3.9+
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tool-registry.git
   cd tool-registry
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the server:
   ```bash
   uvicorn tool_registry.main:app --reload
   ```

5. Navigate to http://localhost:8000/docs to view the API documentation.

## Using the API

### API Overview

The Tool Registry API allows you to:
- Register and manage tools
- Manage agents
- Set up access policies
- Search for tools

### Register a Tool

Here's a quick example to register a tool:

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/tools/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Example Tool",
  "description": "A sample tool for demonstration",
  "api_endpoint": "https://api.example.com/tool",
  "auth_method": "API_KEY",
  "auth_config": {
    "header_name": "X-API-Key"
  },
  "params": {
    "input": {
      "type": "string",
      "description": "Input data for the tool"
    }
  },
  "version": "1.0.0",
  "tags": ["sample", "demo"]
}'
```

### Search for Tools

Search for tools by name or description:

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/tools/search?query=demo'
```

### Create an Agent

Create an agent:

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/agents/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Example Agent",
  "description": "A sample agent for testing",
  "roles": ["user"]
}'
```

### Get Tool Recommendations

Get tool recommendations for an agent:

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/recommendations/agent/{agent_id}'
```

## Development Tips

### Testing

Run tests with:

```bash
python -m pytest
```

### API Documentation

The API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database

By default, the application uses SQLite. For production, configure a PostgreSQL database by setting the `DATABASE_URL` environment variable.

## Next Steps

- Check the [API Reference](api_reference.md) for detailed API information
- Read the [Deployment Guide](deployment_guide.md) for production deployment
- Review the [Security Guide](security_guide.md) for security considerations

## Troubleshooting

- If you encounter database errors, ensure your database is properly configured
- For authentication issues, check that you're using the correct credentials (currently, authentication is disabled for development)
- If you're having trouble with tool registration, verify that your tool payload matches the expected schema 