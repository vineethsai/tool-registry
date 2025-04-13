# API Reference

This document provides a comprehensive reference for the GenAI Tool Registry API endpoints.

## Authentication

### Get Token

Obtain a JWT authentication token.

```
POST /token
```

**Request Body:**
```json
{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Create Agent

Create a new agent (user, service, etc.) in the system.

```
POST /agents
```

**Request Headers:**
```
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "Agent Name",
  "description": "Agent description",
  "metadata": {
    "owner": "team-name",
    "environment": "production"
  },
  "roles": ["tool_user"],
  "permissions": ["access_tool:*"]
}
```

**Response:**
```json
{
  "agent_id": "00000000-0000-0000-0000-000000000001",
  "name": "Agent Name",
  "token": "api-token",
  "expires_at": "2023-12-31T23:59:59"
}
```

## Tool Registry

### Register Tool

Register a new tool in the registry.

```
POST /tools/
```

**Request Headers:**
```
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "Example Tool",
  "description": "A tool for example purposes",
  "version": "1.0.0",
  "tool_metadata": {
    "schema_version": "1.0",
    "inputs": {
      "text": {
        "type": "string"
      }
    },
    "outputs": {
      "result": {
        "type": "string"
      }
    }
  }
}
```

**Response:**
```json
{
  "tool_id": "00000000-0000-0000-0000-000000000001",
  "name": "Example Tool",
  "description": "A tool for example purposes",
  "version": "1.0.0",
  "tool_metadata_rel": {
    "schema_version": "1.0",
    "inputs": {
      "text": {
        "type": "string"
      }
    },
    "outputs": {
      "result": {
        "type": "string"
      }
    }
  },
  "endpoint": "/api/tools/example-tool",
  "auth_required": true,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### List Tools

List all tools in the registry.

```
GET /tools
```

**Request Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "tool_id": "00000000-0000-0000-0000-000000000001",
    "name": "Example Tool",
    "description": "A tool for example purposes",
    "version": "1.0.0",
    "tool_metadata_rel": {
      "schema_version": "1.0",
      "inputs": {
        "text": {
          "type": "string"
        }
      },
      "outputs": {
        "result": {
          "type": "string"
        }
      }
    },
    "endpoint": "/api/tools/example-tool",
    "auth_required": true,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
]
```

### Search Tools

Search for tools by name, description, or tags.

```
GET /tools/search?query={search_term}
```

**Request Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "tool_id": "00000000-0000-0000-0000-000000000001",
    "name": "Example Tool",
    "description": "A tool for example purposes",
    "version": "1.0.0",
    "tool_metadata_rel": {
      "schema_version": "1.0",
      "inputs": {
        "text": {
          "type": "string"
        }
      },
      "outputs": {
        "result": {
          "type": "string"
        }
      }
    },
    "endpoint": "/api/tools/example-tool",
    "auth_required": true,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
]
```

### Get Tool

Get details for a specific tool by ID.

```
GET /tools/{tool_id}
```

**Request Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "tool_id": "00000000-0000-0000-0000-000000000001",
  "name": "Example Tool",
  "description": "A tool for example purposes",
  "version": "1.0.0",
  "tool_metadata_rel": {
    "schema_version": "1.0",
    "inputs": {
      "text": {
        "type": "string"
      }
    },
    "outputs": {
      "result": {
        "type": "string"
      }
    }
  },
  "endpoint": "/api/tools/example-tool",
  "auth_required": true,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Update Tool

Update an existing tool.

```
PUT /tools/{tool_id}
```

**Request Headers:**
```
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "Updated Tool",
  "description": "An updated tool",
  "version": "1.1.0",
  "tool_metadata": {
    "schema_version": "1.0",
    "inputs": {
      "text": {
        "type": "string"
      },
      "count": {
        "type": "integer"
      }
    },
    "outputs": {
      "result": {
        "type": "string"
      }
    }
  }
}
```

**Response:**
```json
true
```

### Delete Tool

Delete a tool from the registry.

```
DELETE /tools/{tool_id}
```

**Request Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
true
```

### Request Tool Access

Request temporary credentials to access a tool.

```
POST /tools/{tool_id}/access
```

**Request Headers:**
```
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "duration": 15,
  "scopes": ["read", "write"]
}
```

**Response:**
```json
{
  "credential_id": "00000000-0000-0000-0000-000000000001",
  "agent_id": "00000000-0000-0000-0000-000000000001",
  "tool_id": "00000000-0000-0000-0000-000000000001",
  "token": "tool-access-token",
  "expires_at": "2023-01-01T00:15:00",
  "created_at": "2023-01-01T00:00:00",
  "scopes": ["read", "write"]
}
```

## Health Check

### System Health

Check the health of the system.

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "database": "healthy"
  }
}
```

## Error Responses

All API endpoints return appropriate HTTP status codes and error details in case of failures:

### 400 Bad Request

```json
{
  "detail": "Invalid request: missing required field 'name'"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Not authorized to register tools"
}
```

### 404 Not Found

```json
{
  "detail": "Tool not found"
}
```

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded"
}
```

The response will include a `Retry-After` header indicating when the client can retry the request.

## Rate Limiting

API endpoints are subject to rate limiting. The default limits are:

- 100 requests per minute per API key
- 1000 requests per hour per API key

When rate limits are exceeded, the API will return a 429 Too Many Requests response with a Retry-After header.

## Pagination

List endpoints support pagination with the following query parameters:

- `offset`: The number of items to skip (default: 0)
- `limit`: The maximum number of items to return (default: 100, max: 1000)

Example:

```
GET /tools?offset=100&limit=50
```

## Authentication

All API endpoints except `/health` require authentication. Include a JWT token in the Authorization header:

```
Authorization: Bearer {token}
```

Tokens are obtained by calling the `/token` endpoint with valid credentials. Tokens expire after 30 minutes by default. 