from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl

class Tool(BaseModel):
    """Model representing a registered tool in the system."""
    tool_id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    api_endpoint: HttpUrl
    auth_method: str  # Enum: API_KEY, OAUTH2, MTLS, NONE
    auth_config: dict
    params: dict
    cost_limit: Optional[dict] = None
    tags: List[str] = Field(default_factory=list)
    version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner: str
    policy_id: List[UUID] = Field(default_factory=list)

class Agent(BaseModel):
    """Model representing a GenAI agent in the system."""
    agent_id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Policy(BaseModel):
    """Model representing an authorization policy."""
    policy_id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    rules: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Credential(BaseModel):
    """Model representing temporary credentials for tool access."""
    credential_id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    tool_id: UUID
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow) 