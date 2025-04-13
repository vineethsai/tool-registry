# Tool Registry Usage Examples

This document provides practical code examples for common operations with the Tool Registry API.

## Authentication

Before using the API, you need to authenticate and get an access token:

```python
import requests

auth_url = "http://localhost:8000/auth/token"
credentials = {
    "username": "user@example.com",
    "password": "your_password"
}

auth_response = requests.post(auth_url, data=credentials)
token = auth_response.json()["access_token"]

# Create headers for authenticated requests
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

## Working with Tools

### List Available Tools

```python
import requests

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Basic listing
response = requests.get(f"{api_url}/tools", headers=headers)
tools = response.json()["items"]
print(f"Found {len(tools)} tools")

# With pagination
response = requests.get(
    f"{api_url}/tools",
    headers=headers,
    params={"page": 1, "page_size": 10}
)
tools = response.json()["items"]
total = response.json()["total"]
print(f"Page 1: {len(tools)} of {total} tools")

# With filtering
response = requests.get(
    f"{api_url}/tools",
    headers=headers,
    params={"tags": "ai,generation"}
)
ai_tools = response.json()["items"]
print(f"Found {len(ai_tools)} AI generation tools")
```

### Register a New Tool

```python
import requests
import json
import uuid

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

tool_data = {
    "name": "Text Summarizer",
    "description": "Summarizes long text into concise points",
    "api_endpoint": "https://api.example.com/summarize",
    "auth_method": "bearer",
    "auth_config": {
        "token_placeholder": "${BEARER_TOKEN}"
    },
    "params": {
        "text": {"type": "string", "required": True},
        "max_length": {"type": "integer", "required": False, "default": 100},
        "format": {"type": "string", "required": False, "default": "paragraph", 
                   "allowed_values": ["paragraph", "bullet_points"]}
    },
    "version": "1.0.0",
    "tags": ["text", "summarization", "nlp"]
}

response = requests.post(
    f"{api_url}/tools",
    headers=headers,
    data=json.dumps(tool_data)
)

new_tool = response.json()
print(f"Tool registered with ID: {new_tool['tool_id']}")
```

### Get Tool Details

```python
import requests

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id

response = requests.get(f"{api_url}/tools/{tool_id}", headers=headers)

if response.status_code == 200:
    tool = response.json()
    print(f"Tool name: {tool['name']}")
    print(f"Description: {tool['description']}")
    print(f"Endpoint: {tool['api_endpoint']}")
    print(f"Version: {tool['version']}")
    print(f"Tags: {', '.join(tool['tags'])}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Update an Existing Tool

```python
import requests
import json

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id

update_data = {
    "description": "Updated description for the tool",
    "version": "1.1.0",
    "tags": ["text", "summarization", "nlp", "ai"]
}

response = requests.put(
    f"{api_url}/tools/{tool_id}",
    headers=headers,
    data=json.dumps(update_data)
)

if response.status_code == 200:
    updated_tool = response.json()
    print(f"Tool updated: {updated_tool['name']} (v{updated_tool['version']})")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Delete a Tool

```python
import requests

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id

response = requests.delete(f"{api_url}/tools/{tool_id}", headers=headers)

if response.status_code == 204:
    print(f"Tool {tool_id} deleted successfully")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Search for Tools

```python
import requests

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Search by query string
search_query = "image generation"
response = requests.get(
    f"{api_url}/tools/search",
    headers=headers,
    params={"query": search_query}
)

results = response.json()["items"]
print(f"Found {len(results)} tools matching '{search_query}'")
for tool in results:
    print(f"- {tool['name']} (v{tool['version']})")
```

## Working with Policies

### Create an Access Policy

```python
import requests
import json
import uuid

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id

policy_data = {
    "name": "Data Science Team Access",
    "description": "Access policy for data science team members",
    "tool_id": tool_id,
    "allowed_scopes": ["read", "execute"],
    "conditions": {
        "max_requests_per_day": 1000,
        "restricted_params": {
            "max_length": {"max": 500}
        }
    },
    "rules": {
        "require_approval": False,
        "log_usage": True,
        "valid_until": "2023-12-31T23:59:59Z"
    },
    "priority": 10
}

response = requests.post(
    f"{api_url}/policies",
    headers=headers,
    data=json.dumps(policy_data)
)

new_policy = response.json()
print(f"Policy created with ID: {new_policy['policy_id']}")
```

### List Policies for a Tool

```python
import requests

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id

response = requests.get(
    f"{api_url}/tools/{tool_id}/policies",
    headers=headers
)

policies = response.json()["items"]
print(f"Found {len(policies)} policies for tool {tool_id}")
for policy in policies:
    print(f"- {policy['name']}: {policy['description']}")
```

## Working with Agents

### Register a New Agent

```python
import requests
import json

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

agent_data = {
    "name": "Data Science Bot",
    "description": "Automated agent for data analysis tasks",
    "agent_type": "bot",
    "metadata": {
        "team": "Data Science",
        "department": "Research",
        "contact_email": "data.team@example.com"
    }
}

response = requests.post(
    f"{api_url}/agents",
    headers=headers,
    data=json.dumps(agent_data)
)

new_agent = response.json()
print(f"Agent created with ID: {new_agent['agent_id']}")
```

### Grant Access to a Tool

```python
import requests
import json

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

agent_id = "5ea85f64-5717-4562-b3fc-2c963f66afa7"  # Replace with actual agent_id
tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id
policy_id = "7fa85f64-5717-4562-b3fc-2c963f66afa8"  # Replace with actual policy_id

access_request = {
    "agent_id": agent_id,
    "tool_id": tool_id,
    "policy_id": policy_id,
    "justification": "Required for automated data analysis pipeline"
}

response = requests.post(
    f"{api_url}/access/request",
    headers=headers,
    data=json.dumps(access_request)
)

if response.status_code == 200:
    result = response.json()
    print(f"Access granted: {result['status']}")
    print(f"Access request ID: {result['request_id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Check Agent's Access to a Tool

```python
import requests

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

agent_id = "5ea85f64-5717-4562-b3fc-2c963f66afa7"  # Replace with actual agent_id
tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id

response = requests.get(
    f"{api_url}/access/validate",
    headers=headers,
    params={"agent_id": agent_id, "tool_id": tool_id}
)

if response.status_code == 200:
    access_info = response.json()
    print(f"Access status: {access_info['has_access']}")
    if access_info['has_access']:
        print(f"Allowed scopes: {', '.join(access_info['allowed_scopes'])}")
        print(f"Applied policy: {access_info['policy_name']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Working with Credentials

### Create Credentials for a Tool

```python
import requests
import json

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

agent_id = "5ea85f64-5717-4562-b3fc-2c963f66afa7"  # Replace with actual agent_id
tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id

credential_data = {
    "agent_id": agent_id,
    "tool_id": tool_id,
    "credential_type": "api_key",
    "credential_value": {
        "api_key": "sk_test_abcdefghijklmnopqrstuvwxyz123456789"
    },
    "expires_at": "2023-12-31T23:59:59Z"
}

response = requests.post(
    f"{api_url}/credentials",
    headers=headers,
    data=json.dumps(credential_data)
)

if response.status_code == 201:
    new_credential = response.json()
    print(f"Credential created with ID: {new_credential['credential_id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### List Agent's Credentials

```python
import requests

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

agent_id = "5ea85f64-5717-4562-b3fc-2c963f66afa7"  # Replace with actual agent_id

response = requests.get(
    f"{api_url}/agents/{agent_id}/credentials",
    headers=headers
)

if response.status_code == 200:
    credentials = response.json()["items"]
    print(f"Found {len(credentials)} credentials for agent {agent_id}")
    for cred in credentials:
        print(f"- {cred['credential_id']} for tool {cred['tool_id']}")
        print(f"  Type: {cred['credential_type']}")
        print(f"  Expires: {cred['expires_at']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Viewing Usage Logs

```python
import requests
from datetime import datetime, timedelta

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Get yesterday's date in ISO format
yesterday = (datetime.now() - timedelta(days=1)).isoformat()

# Get usage logs for a specific tool
tool_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Replace with actual tool_id

response = requests.get(
    f"{api_url}/logs",
    headers=headers,
    params={
        "tool_id": tool_id,
        "start_date": yesterday
    }
)

if response.status_code == 200:
    logs = response.json()["items"]
    print(f"Found {len(logs)} usage logs for tool {tool_id} since yesterday")
    for log in logs:
        print(f"- {log['timestamp']}: Agent {log['agent_id']} used {log['scope']}")
        print(f"  Status: {log['status']}, Duration: {log['duration_ms']}ms")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Using the Python SDK (Alternative Approach)

The Tool Registry also provides a Python SDK for easier integration:

```python
from tool_registry import ToolRegistryClient

# Initialize client
client = ToolRegistryClient(
    base_url="http://localhost:8000/api/v1",
    api_key="your_api_key"  # Or use username/password authentication
)

# List available tools
tools = client.list_tools(tags=["ai"])
print(f"Found {len(tools)} AI tools")

# Register a new tool
new_tool = client.register_tool(
    name="Text Translator",
    description="Translates text between languages",
    api_endpoint="https://api.example.com/translate",
    auth_method="api_key",
    params={
        "text": {"type": "string", "required": True},
        "source_lang": {"type": "string", "required": False, "default": "auto"},
        "target_lang": {"type": "string", "required": True}
    },
    version="1.0.0",
    tags=["text", "translation"]
)
print(f"Tool registered with ID: {new_tool.tool_id}")

# Create a policy
policy = client.create_policy(
    name="Translation API Policy",
    tool_id=new_tool.tool_id,
    allowed_scopes=["read", "execute"],
    conditions={
        "max_requests_per_minute": 60,
        "max_text_length": 5000
    }
)
print(f"Policy created with ID: {policy.policy_id}")

# Register an agent
agent = client.register_agent(
    name="Translation Bot",
    agent_type="bot",
    description="Automated translation service"
)
print(f"Agent registered with ID: {agent.agent_id}")

# Grant access
access = client.grant_access(
    agent_id=agent.agent_id,
    tool_id=new_tool.tool_id,
    policy_id=policy.policy_id
)
print(f"Access granted: {access.status}")
```

## Error Handling

```python
import requests

api_url = "http://localhost:8000/api/v1"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    # Try to get a non-existent tool
    response = requests.get(
        f"{api_url}/tools/not-a-real-id",
        headers=headers
    )
    
    response.raise_for_status()  # Raise exception for 4XX/5XX responses
    
    tool = response.json()
    print(f"Tool found: {tool['name']}")
    
except requests.exceptions.HTTPError as e:
    status_code = e.response.status_code
    error_detail = e.response.json().get("detail", "Unknown error")
    
    if status_code == 404:
        print(f"Tool not found: {error_detail}")
    elif status_code == 401:
        print(f"Authentication error: {error_detail}")
    elif status_code == 403:
        print(f"Permission denied: {error_detail}")
    else:
        print(f"API error ({status_code}): {error_detail}")
        
except requests.exceptions.ConnectionError:
    print("Connection error: Could not connect to the API server")
    
except Exception as e:
    print(f"Unexpected error: {str(e)}") 