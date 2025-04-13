# Database Schema Documentation

This document provides a detailed overview of the database models used in the GenAI Tool Registry.

## Overview

The Tool Registry uses SQLAlchemy as its ORM (Object-Relational Mapping) system. All models are defined in the `tool_registry/models/` directory and inherit from a common `Base` class.

The database schema includes the following main entities:

1. **Tool**: Represents a registered AI tool with its configuration
2. **ToolMetadata**: Contains additional metadata about a tool
3. **Agent**: Represents a user or service that interacts with tools
4. **Policy**: Defines access rules for tools
5. **Credential**: Stores credentials issued for tool access
6. **AccessLog**: Records access attempts to tools

## Entity Relationship Diagram

```
+-------------+       +---------------+
|    Agent    |-------|     Tool      |
+-------------+       +---------------+
      |  |                   |
      |  |                   |
      |  |     +--------+    |
      |  |-----|  Policy|    |
      |        +--------+    |
      |                      |
+------------+      +-------------+
| Credential |      | ToolMetadata|
+------------+      +-------------+
      |
      |
+------------+
| AccessLog  |
+------------+
```

## Model Definitions

### Tool

**File**: `tool_registry/models/tool.py`

The Tool model is the central entity in the system, representing a registered AI tool.

```python
class Tool(Base):
    __tablename__ = "tools"
    
    tool_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    api_endpoint = Column(String, nullable=False)
    auth_method = Column(String, nullable=False)
    auth_config = Column(JSON, nullable=False, default=dict)
    params = Column(JSON, nullable=False, default=dict)
    version = Column(String, nullable=False)
    tags = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    allowed_scopes = Column(JSON, default=list)
    
    # Foreign keys
    owner_id = Column(UUID(as_uuid=True), ForeignKey('agents.agent_id'), nullable=False)
    
    # Relationships
    owner = relationship("Agent", back_populates="owned_tools")
    policies = relationship("Policy", back_populates="tool")
    tool_metadata_rel = relationship("ToolMetadata", back_populates="tool", uselist=False, cascade="all, delete-orphan")
    credentials = relationship("Credential", back_populates="tool", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="tool", cascade="all, delete-orphan")
```

#### Key Fields:

- `tool_id`: Unique identifier (UUID)
- `name`: Tool name (must be unique)
- `description`: Optional description of the tool
- `api_endpoint`: URL endpoint where the tool can be accessed
- `auth_method`: Authentication method required (e.g., "api_key", "oauth2")
- `auth_config`: JSON configuration for authentication
- `params`: JSON schema for required parameters
- `version`: Tool version string
- `tags`: List of tags for categorization
- `allowed_scopes`: List of available scopes for this tool

### ToolMetadata

**File**: `tool_registry/models/tool_metadata.py`

Contains additional metadata about a tool that doesn't need to be queried as frequently.

```python
class ToolMetadata(Base):
    __tablename__ = "tool_metadata"
    
    metadata_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey('tools.tool_id'), unique=True, nullable=False)
    schema_type = Column(String, nullable=True)
    schema_version = Column(String, nullable=True)
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    examples = Column(JSON, nullable=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    avg_response_time = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    custom_metrics = Column(JSON, nullable=True, default=dict)
    
    # Relationships
    tool = relationship("Tool", back_populates="tool_metadata_rel")
```

#### Key Fields:

- `metadata_id`: Unique identifier (UUID)
- `tool_id`: Foreign key to the associated tool
- `schema_type`: Type of schema (e.g., "openapi", "jsonschema")
- `schema_version`: Version of the schema
- `inputs`: JSON schema for input parameters
- `outputs`: JSON schema for output format
- `examples`: Example inputs and outputs
- `usage_count`: Number of times the tool has been used
- `last_used`: Timestamp of last usage
- `avg_response_time`: Average response time in seconds
- `error_rate`: Error rate as a percentage
- `custom_metrics`: Custom metrics as JSON

### Agent

**File**: `tool_registry/models/agent.py`

Represents a user or service that interacts with tools.

```python
class Agent(Base):
    __tablename__ = "agents"
    
    agent_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    api_key = Column(String, nullable=True)
    roles = Column(JSON, nullable=False, default=list)
    permissions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    owned_tools = relationship("Tool", back_populates="owner")
    credentials = relationship("Credential", back_populates="agent", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="agent", cascade="all, delete-orphan")
    created_policies = relationship("Policy", foreign_keys="Policy.created_by", back_populates="creator")
```

#### Key Fields:

- `agent_id`: Unique identifier (UUID)
- `name`: Agent name
- `description`: Optional description
- `api_key`: API key for authentication
- `roles`: List of roles assigned to the agent
- `permissions`: List of explicit permissions

### Policy

**File**: `tool_registry/models/policy.py`

Defines access rules for tools.

```python
class Policy(Base):
    __tablename__ = "policies"
    
    policy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey('tools.tool_id'), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('agents.agent_id'), nullable=True)
    allowed_scopes = Column(JSON, default=list)
    conditions = Column(JSON, default=dict)
    rules = Column(JSON, default=dict)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tool = relationship("Tool", back_populates="policies")
    creator = relationship("Agent", foreign_keys=[created_by], back_populates="created_policies")
    access_logs = relationship("AccessLog", back_populates="policy", cascade="all, delete-orphan")
```

#### Key Fields:

- `policy_id`: Unique identifier (UUID)
- `name`: Policy name
- `description`: Optional description
- `tool_id`: Foreign key to the associated tool
- `created_by`: Foreign key to the agent who created the policy
- `allowed_scopes`: List of scopes allowed by this policy
- `conditions`: JSON object with conditions for policy evaluation
- `rules`: JSON object with rules for policy evaluation
- `priority`: Policy priority (higher numbers have higher priority)

### Credential

**File**: `tool_registry/models/credential.py`

Stores credentials issued for tool access.

```python
class Credential(Base):
    __tablename__ = "credentials"
    
    credential_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.agent_id'), nullable=False)
    tool_id = Column(UUID(as_uuid=True), ForeignKey('tools.tool_id'), nullable=False)
    token = Column(String, nullable=False)
    scopes = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="credentials")
    tool = relationship("Tool", back_populates="credentials")
    access_logs = relationship("AccessLog", back_populates="credential", cascade="all, delete-orphan")
```

#### Key Fields:

- `credential_id`: Unique identifier (UUID)
- `agent_id`: Foreign key to the agent
- `tool_id`: Foreign key to the tool
- `token`: Token string used for authentication
- `scopes`: List of scopes granted by this credential
- `created_at`: Creation timestamp
- `expires_at`: Expiration timestamp
- `is_revoked`: Whether the credential has been revoked
- `metadata`: Additional metadata as JSON

### AccessLog

**File**: `tool_registry/models/access_log.py`

Records access attempts to tools.

```python
class AccessLog(Base):
    __tablename__ = "access_logs"
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.agent_id'), nullable=False)
    tool_id = Column(UUID(as_uuid=True), ForeignKey('tools.tool_id'), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey('policies.policy_id'), nullable=True)
    credential_id = Column(UUID(as_uuid=True), ForeignKey('credentials.credential_id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String, nullable=False)
    status = Column(String, nullable=False)
    scopes = Column(JSON, nullable=True)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    request_ip = Column(String, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="access_logs")
    tool = relationship("Tool", back_populates="access_logs")
    policy = relationship("Policy", back_populates="access_logs")
    credential = relationship("Credential", back_populates="access_logs")
```

#### Key Fields:

- `log_id`: Unique identifier (UUID)
- `agent_id`: Foreign key to the agent
- `tool_id`: Foreign key to the tool
- `policy_id`: Foreign key to the policy (if any)
- `credential_id`: Foreign key to the credential (if any)
- `timestamp`: Timestamp of the access attempt
- `action`: Action attempted (e.g., "read", "write")
- `status`: Status of the attempt (e.g., "success", "denied")
- `scopes`: Scopes requested/used
- `request_data`: Request data as JSON
- `response_data`: Response data as JSON
- `request_ip`: IP address of the requester

## Important Notes on SQLAlchemy Usage

### Reserved Attribute Names

SQLAlchemy reserves certain attribute names that should not be used in models:

- `metadata`
- `query`
- `__table__`

For example, we use `tool_metadata_rel` instead of `metadata` for the relationship attribute in the Tool model.

### Session Management

Always use context managers or try/finally blocks when working with database sessions:

```python
session = next(db.get_session())
try:
    # Do database operations
    session.commit()
finally:
    session.close()
```

### JSON Fields

When using JSON fields, it's important to provide a default value:

```python
tags = Column(JSON, nullable=False, default=list)
auth_config = Column(JSON, nullable=False, default=dict)
```

### Database Compatibility

Note that some features (like JSON fields) may behave differently across database backends. The codebase is designed to work with:

- SQLite (for development)
- PostgreSQL (recommended for production)
- MySQL (also supported) 