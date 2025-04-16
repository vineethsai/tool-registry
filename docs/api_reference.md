# API Reference

This document provides a reference for the Tool Registry REST API endpoints.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000/api/v1
```

For production deployments, use your domain name:

```
https://your-domain.com/api/v1
```

## Authentication

> **IMPORTANT NOTE**: Authentication is currently disabled for development purposes. API endpoints can be accessed without authentication tokens. The credential management system remains in place but is not enforced.

The Tool Registry API uses JWT-based authentication. To authenticate:

While authentication is disabled, the following endpoints still exist to maintain API compatibility:

```
POST /token
POST /auth/api-key
```

Both will return a dummy token that can be used in subsequent requests if needed:

```json
{
  "access_token": "test_token",
  "token_type": "bearer"
}
```

### Self-Registration

Register as a new user:

```
POST /register
```

Request body:
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password",
  "name": "New User",
  "organization": "Example Org"
}
```

### Generate API Key

Create an API key for programmatic access:

```
POST /api-keys
```

Request body:
```json
{
  "name": "My Application Key",
  "description": "API key for my application",
  "expires_in_days": 90,
  "permissions": ["access_tool:public"]
}
```

## Response Format

All responses follow a standard format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "errors": null
}
```

Or in case of errors:

```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "errors": { ... }
}
```

## Pagination

List endpoints support pagination with the following query parameters:

- `page`: Page number (starting from 1)
- `page_size`: Number of items per page

Response includes pagination metadata:

```json
{
  "items": [ ... ],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "pages": 10
}
```

## Tool Endpoints

### List Tools

Returns a list of available tools.

```
GET /tools
```

Query parameters:
- `tags`: Filter by comma-separated tags
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

Response:

```json
{
  "items": [
    {
      "tool_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Image Generator",
      "description": "Generates images from text prompts",
      "api_endpoint": "https://api.example.com/generate",
      "version": "1.0.0",
      "tags": ["image", "generation", "ai"],
      "created_at": "2023-01-15T14:30:00Z",
      "updated_at": "2023-01-15T14:30:00Z"
    },
    // More tools...
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

### Get Tool

Returns detailed information about a specific tool.

```
GET /tools/{tool_id}
```

Path parameters:
- `tool_id`: UUID of the tool

Response:

```json
{
  "tool_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Image Generator",
  "description": "Generates images from text prompts",
  "api_endpoint": "https://api.example.com/generate",
  "auth_method": "oauth2",
  "auth_config": {
    "token_url": "https://api.example.com/oauth/token",
    "client_id_placeholder": "${CLIENT_ID}",
    "scope": "image:generate"
  },
  "params": {
    "prompt": {
      "type": "string",
      "required": true,
      "description": "Text description of the image"
    },
    "style": {
      "type": "string",
      "required": false,
      "default": "realistic",
      "allowed_values": ["realistic", "cartoon", "sketch"]
    },
    "size": {
      "type": "string",
      "required": false,
      "default": "512x512"
    }
  },
  "version": "1.0.0",
  "tags": ["image", "generation", "ai"],
  "created_at": "2023-01-15T14:30:00Z",
  "updated_at": "2023-01-15T14:30:00Z",
  "owner_id": "5fa85f64-5717-4562-b3fc-2c963f66afa7",
  "is_active": true
}
```

### Register Tool

Registers a new tool in the registry.

```
POST /tools
```

Request body:

```json
{
  "name": "Text Summarizer",
  "description": "Summarizes long text into concise points",
  "api_endpoint": "https://api.example.com/summarize",
  "auth_method": "api_key",
  "auth_config": {
    "header_name": "X-API-Key",
    "key_placeholder": "${API_KEY}"
  },
  "params": {
    "text": {
      "type": "string",
      "required": true
    },
    "length": {
      "type": "integer",
      "required": false,
      "default": 100
    }
  },
  "version": "1.0.0",
  "tags": ["text", "summarization", "nlp"]
}
```

Response:

```json
{
  "tool_id": "4fa85f64-5717-4562-b3fc-2c963f66afa8",
  "name": "Text Summarizer",
  "description": "Summarizes long text into concise points",
  // Other tool properties...
  "created_at": "2023-06-20T10:15:30Z",
  "updated_at": "2023-06-20T10:15:30Z"
}
```

Error Responses:

| Status Code | Description |
|------------|-------------|
| 409 Conflict | A tool with the provided name already exists |

Example error response for duplicate tool:

```json
{
  "detail": "Tool with name 'Text Summarizer' already exists"
}
```

### Update Tool

Updates an existing tool.

```
PUT /tools/{tool_id}
```

Path parameters:
- `tool_id`: UUID of the tool

Request body (all fields optional):

```json
{
  "description": "Updated description",
  "api_endpoint": "https://api.example.com/v2/summarize",
  "version": "1.1.0",
  "tags": ["text", "summarization", "nlp", "ai"]
}
```

Response: Updated tool object

### Delete Tool

Deletes a tool from the registry.

```
DELETE /tools/{tool_id}
```

Path parameters:
- `tool_id`: UUID of the tool

Response status: 204 No Content

### Search Tools

Searches for tools based on a query string.

```
GET /tools/search
```

Query parameters:
- `query`: Search query (searches in name, description, and tags)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

Response: Paginated list of matching tools

## Policy Endpoints

### List Policies

Returns a list of access policies.

```
GET /policies
```

Query parameters:
- `tool_id`: Filter by tool ID
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

Response: Paginated list of policies

### Get Policy

Returns detailed information about a specific policy.

```
GET /policies/{policy_id}
```

Path parameters:
- `policy_id`: UUID of the policy

Response: Policy object

### Create Policy

Creates a new access policy.

```
POST /policies
```

Request body:

```json
{
  "name": "Basic Access",
  "description": "Basic access to the tool with rate limiting",
  "tool_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "allowed_scopes": ["read", "execute"],
  "conditions": {
    "max_requests_per_day": 1000,
    "allowed_hours": {
      "start": "09:00",
      "end": "17:00"
    }
  },
  "rules": {
    "require_approval": false,
    "log_usage": true
  },
  "priority": 10
}
```

Response: Created policy object

### Update Policy

Updates an existing policy.

```
PUT /policies/{policy_id}
```

Path parameters:
- `policy_id`: UUID of the policy

Request body (all fields optional):
- Same fields as create policy

Response: Updated policy object

### Delete Policy

Deletes a policy.

```
DELETE /policies/{policy_id}
```

Path parameters:
- `policy_id`: UUID of the policy

Response status: 204 No Content

## Agent Endpoints

### List Agents

Returns a list of registered agents.

```
GET /agents
```

Query parameters:
- `agent_type`: Filter by agent type (user, service, bot)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

Response: Paginated list of agents

### Get Agent

Returns detailed information about a specific agent.

```
GET /agents/{agent_id}
```

Path parameters:
- `agent_id`: UUID of the agent

Response: Agent object

### Register Agent

Registers a new agent.

```
POST /agents
```

Request body:

```json
{
  "name": "Research Assistant",
  "description": "AI assistant for research tasks",
  "agent_type": "bot",
  "metadata": {
    "team": "Research",
    "department": "AI Lab",
    "capabilities": ["documentation", "search"]
  }
}
```

Response: Created agent object

### Update Agent

Updates an existing agent.

```
PUT /agents/{agent_id}
```

Path parameters:
- `agent_id`: UUID of the agent

Request body (all fields optional):
- Same fields as register agent

Response: Updated agent object

### Delete Agent

Deletes an agent.

```
DELETE /agents/{agent_id}
```

Path parameters:
- `agent_id`: UUID of the agent

Response status: 204 No Content

## Access Control Endpoints

### Request Tool Access

Requests access to a tool for an agent.

```
POST /access/request
```

Request body:

```json
{
  "agent_id": "5fa85f64-5717-4562-b3fc-2c963f66afa7",
  "tool_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "policy_id": "7fa85f64-5717-4562-b3fc-2c963f66afa8",
  "justification": "Required for automated data analysis pipeline"
}
```

Response:

```json
{
  "request_id": "8fa85f64-5717-4562-b3fc-2c963f66afa9",
  "status": "approved",
  "agent_id": "5fa85f64-5717-4562-b3fc-2c963f66afa7",
  "tool_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "policy_id": "7fa85f64-5717-4562-b3fc-2c963f66afa8",
  "created_at": "2023-06-20T11:30:45Z"
}
```

### Validate Access

Checks if an agent has access to a tool.

```
GET /access/validate
```

Query parameters:
- `agent_id`: UUID of the agent
- `tool_id`: UUID of the tool

Response:

```json
{
  "has_access": true,
  "agent_id": "5fa85f64-5717-4562-b3fc-2c963f66afa7",
  "tool_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "allowed_scopes": ["read", "execute"],
  "policy_id": "7fa85f64-5717-4562-b3fc-2c963f66afa8",
  "policy_name": "Basic Access"
}
```

### List Access Requests

Returns a list of access requests.

```
GET /access/requests
```

Query parameters:
- `agent_id`: Filter by agent ID
- `tool_id`: Filter by tool ID
- `status`: Filter by status (pending, approved, rejected)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

Response: Paginated list of access requests

## Credential Endpoints

### Create Credential

Creates a new credential for a tool.

```
POST /credentials
```

Request body:

```json
{
  "agent_id": "5fa85f64-5717-4562-b3fc-2c963f66afa7",
  "tool_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "credential_type": "api_key",
  "credential_value": {
    "api_key": "sk_test_abcdefghijklmnopqrstuvwxyz"
  },
  "expires_at": "2023-12-31T23:59:59Z"
}
```

Response: Created credential object (without sensitive values)

### List Credentials

Returns a list of credentials.

```
GET /credentials
```

Query parameters:
- `agent_id`: Filter by agent ID
- `tool_id`: Filter by tool ID
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

Response: Paginated list of credentials (without sensitive values)

### Get Credential

Returns information about a specific credential.

```
GET /credentials/{credential_id}
```

Path parameters:
- `credential_id`: UUID of the credential

Response: Credential object (without sensitive values)

### Delete Credential

Deletes a credential.

```
DELETE /credentials/{credential_id}
```

Path parameters:
- `credential_id`: UUID of the credential

Response status: 204 No Content

## Usage Logs

### Get Usage Logs

Returns a list of tool usage logs.

```
GET /logs
```

Query parameters:
- `agent_id`: Filter by agent ID
- `tool_id`: Filter by tool ID
- `start_date`: Filter by start date (ISO format)
- `end_date`: Filter by end date (ISO format)
- `status`: Filter by status (success, error)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

Response: Paginated list of usage logs

### Get Usage Statistics

Returns usage statistics for tools.

```
GET /stats/usage
```

Query parameters:
- `tool_id`: Filter by tool ID
- `period`: Aggregation period (day, week, month)
- `start_date`: Filter by start date (ISO format)
- `end_date`: Filter by end date (ISO format)

Response:

```json
{
  "total_requests": 12500,
  "successful_requests": 12250,
  "failed_requests": 250,
  "average_duration_ms": 145,
  "by_period": [
    {
      "period": "2023-06-01",
      "requests": 450,
      "success_rate": 0.98
    },
    // More periods...
  ],
  "by_tool": [
    {
      "tool_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "tool_name": "Image Generator",
      "requests": 8500,
      "success_rate": 0.97
    },
    // More tools...
  ]
}
```

## Status Endpoints

### System Health

Returns system health information.

```
GET /health
```

Response:

```json
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime": 1234567,
  "db_connection": "connected",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "api": {
      "status": "healthy",
      "requests_per_minute": 250
    }
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400  | Bad Request - Invalid input parameters |
| 401  | Unauthorized - Authentication required |
| 403  | Forbidden - Insufficient permissions |
| 404  | Not Found - Resource does not exist |
| 409  | Conflict - Resource already exists |
| 422  | Unprocessable Entity - Validation error |
| 429  | Too Many Requests - Rate limit exceeded |
| 500  | Internal Server Error - Server failure | 