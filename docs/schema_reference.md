# Schema Reference

This document outlines the core data models in the Tool Registry system and their relationships.

## Database Models

### Tool

The `Tool` model represents an AI tool or service registered in the system.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `tool_id` | UUID | Primary key, unique identifier for the tool |
| `name` | String | Name of the tool (must be unique) |
| `description` | String | Detailed description of the tool's functionality |
| `api_endpoint` | String | API endpoint URL where the tool can be accessed |
| `auth_method` | String | Authentication method (api_key, oauth2, bearer, etc.) |
| `auth_config` | JSON | Configuration for authentication (varies by auth_method) |
| `params` | JSON | Parameters the tool accepts (with types, requirements, defaults) |
| `version` | String | Current version of the tool |
| `tags` | Array | List of tags for categorization and search |
| `owner_id` | UUID | Reference to the agent that owns the tool |
| `created_at` | DateTime | When the tool was registered |
| `updated_at` | DateTime | When the tool was last updated |
| `is_active` | Boolean | Whether the tool is currently active |
| `allowed_scopes` | Array | List of allowed access scopes |

**Relationships:**

- `owner` - One-to-one relationship with `Agent`
- `policies` - One-to-many relationship with `Policy`
- `credentials` - One-to-many relationship with `Credential`
- `access_logs` - One-to-many relationship with `AccessLog`
- `metadata` - One-to-one relationship with `ToolMetadata`

### Agent

The `Agent` model represents an entity that can access tools, which could be a user, service, or AI system.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | UUID | Primary key, unique identifier for the agent |
| `name` | String | Name of the agent |
| `description` | String | Description of the agent |
| `agent_type` | String | Type of agent (user, service, bot) |
| `metadata` | JSON | Additional information about the agent |
| `created_at` | DateTime | When the agent was created |
| `updated_at` | DateTime | When the agent was last updated |
| `is_active` | Boolean | Whether the agent is currently active |
| `created_by` | UUID | Reference to the agent that created this agent |

**Relationships:**

- `creator` - Self-referential relationship to `Agent`
| `owned_tools` - One-to-many relationship with `Tool`
- `policies` - One-to-many relationship with `Policy`
- `credentials` - One-to-many relationship with `Credential`
- `access_logs` - One-to-many relationship with `AccessLog`
- `access_requests` - One-to-many relationship with `AccessRequest`

### Policy

The `Policy` model defines access control rules for tools.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `policy_id` | UUID | Primary key, unique identifier for the policy |
| `name` | String | Name of the policy |
| `description` | String | Description of the policy |
| `tool_id` | UUID | Reference to the tool this policy applies to |
| `created_by` | UUID | Reference to the agent that created this policy |
| `allowed_scopes` | JSON | List of access scopes allowed by this policy |
| `conditions` | JSON | Conditions that must be met for access (rate limits, time restrictions) |
| `rules` | JSON | Additional rules for access control |
| `priority` | Integer | Priority of the policy (higher values take precedence) |
| `created_at` | DateTime | When the policy was created |
| `updated_at` | DateTime | When the policy was last updated |
| `is_active` | Boolean | Whether the policy is currently active |

**Relationships:**

- `tool` - Many-to-one relationship with `Tool`
- `creator` - Many-to-one relationship with `Agent`
- `access_logs` - One-to-many relationship with `AccessLog`
- `access_requests` - One-to-many relationship with `AccessRequest`

### Credential

The `Credential` model stores authentication credentials for accessing tools.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `credential_id` | UUID | Primary key, unique identifier for the credential |
| `agent_id` | UUID | Reference to the agent that owns this credential |
| `tool_id` | UUID | Reference to the tool this credential is for |
| `credential_type` | String | Type of credential (api_key, oauth_token, etc.) |
| `credential_value` | JSON | Encrypted credential values |
| `created_at` | DateTime | When the credential was created |
| `updated_at` | DateTime | When the credential was last updated |
| `expires_at` | DateTime | When the credential expires |
| `is_active` | Boolean | Whether the credential is currently active |

**Relationships:**

- `agent` - Many-to-one relationship with `Agent`
- `tool` - Many-to-one relationship with `Tool`

### AccessLog

The `AccessLog` model records tool usage history.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `log_id` | UUID | Primary key, unique identifier for the log entry |
| `agent_id` | UUID | Reference to the agent that accessed the tool |
| `tool_id` | UUID | Reference to the tool that was accessed |
| `policy_id` | UUID | Reference to the policy that was applied |
| `timestamp` | DateTime | When the access occurred |
| `scope` | String | The scope that was used for access |
| `request_data` | JSON | Request data sent to the tool (sanitized) |
| `status` | String | Result status (success, error) |
| `error_message` | String | Error message if access failed |
| `duration_ms` | Integer | Duration of the request in milliseconds |
| `ip_address` | String | IP address of the requester |
| `user_agent` | String | User agent string |

**Relationships:**

- `agent` - Many-to-one relationship with `Agent`
- `tool` - Many-to-one relationship with `Tool`
- `policy` - Many-to-one relationship with `Policy`

### AccessRequest

The `AccessRequest` model represents a request for tool access.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | UUID | Primary key, unique identifier for the request |
| `agent_id` | UUID | Reference to the agent requesting access |
| `tool_id` | UUID | Reference to the tool being requested |
| `policy_id` | UUID | Reference to the policy being requested |
| `justification` | String | Reason for requesting access |
| `status` | String | Status of the request (pending, approved, rejected) |
| `reviewed_by` | UUID | Reference to the agent that reviewed the request |
| `review_notes` | String | Notes from the reviewer |
| `created_at` | DateTime | When the request was created |
| `updated_at` | DateTime | When the request was last updated |

**Relationships:**

- `agent` - Many-to-one relationship with `Agent`
- `tool` - Many-to-one relationship with `Tool`
- `policy` - Many-to-one relationship with `Policy`
- `reviewer` - Many-to-one relationship with `Agent`

### ToolMetadata

The `ToolMetadata` model stores additional metadata about tools.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `metadata_id` | UUID | Primary key, unique identifier for the metadata |
| `tool_id` | UUID | Reference to the tool |
| `documentation_url` | String | URL to the tool's documentation |
| `support_contact` | String | Contact information for support |
| `pricing_info` | JSON | Information about pricing tiers |
| `usage_examples` | JSON | Example usage scenarios |
| `compatibility` | JSON | Compatibility information |
| `performance_metrics` | JSON | Performance benchmarks |
| `created_at` | DateTime | When the metadata was created |
| `updated_at` | DateTime | When the metadata was last updated |

**Relationships:**

- `tool` - One-to-one relationship with `Tool`

## API Request/Response Models

These Pydantic models are used for API request validation and response serialization.

### ToolCreate

Used when registering a new tool:

```python
class ToolCreate(BaseModel):
    name: str
    description: str
    api_endpoint: str
    auth_method: str
    auth_config: Dict[str, Any] = {}
    params: Dict[str, Dict[str, Any]] = {}
    version: str
    tags: List[str] = []
    owner_id: Optional[UUID] = None
    allowed_scopes: List[str] = []
```

### ToolResponse

Returned when retrieving tool information:

```python
class ToolResponse(BaseModel):
    tool_id: UUID
    name: str
    description: str
    api_endpoint: str
    auth_method: str
    auth_config: Dict[str, Any]
    params: Dict[str, Dict[str, Any]]
    version: str
    tags: List[str]
    owner_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    allowed_scopes: List[str]
```

### AgentCreate

Used when registering a new agent:

```python
class AgentCreate(BaseModel):
    name: str
    description: str
    agent_type: str  # user, service, bot
    metadata: Dict[str, Any] = {}
```

### PolicyCreate

Used when creating a new access policy:

```python
class PolicyCreate(BaseModel):
    name: str
    description: str
    tool_id: UUID
    allowed_scopes: List[str] = []
    conditions: Dict[str, Any] = {}
    rules: Dict[str, Any] = {}
    priority: int = 0
```

### AccessRequestCreate

Used when requesting access to a tool:

```python
class AccessRequestCreate(BaseModel):
    agent_id: UUID
    tool_id: UUID
    policy_id: UUID
    justification: str
```

### CredentialCreate

Used when creating a new credential:

```python
class CredentialCreate(BaseModel):
    agent_id: UUID
    tool_id: UUID
    credential_type: str
    credential_value: Dict[str, Any]
    expires_at: Optional[datetime] = None
```

## Relationships Diagram

```
┌─────────┐     ┌──────────┐     ┌──────────┐
│  Agent  │────▶│   Tool   │◀────│  Policy  │
└─────────┘     └──────────┘     └──────────┘
     ▲               ▲                ▲
     │               │                │
     ▼               ▼                ▼
┌─────────┐     ┌──────────┐     ┌──────────┐
│Credential│     │AccessLog │     │AccessReq │
└─────────┘     └──────────┘     └──────────┘
                     ▲
                     │
                     ▼
               ┌──────────┐
               │ToolMetadata│
               └──────────┘
``` 