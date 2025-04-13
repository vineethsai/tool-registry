from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class RegistrationRequest(BaseModel):
    """Request model for self-registration."""
    username: str
    email: str
    password: str
    name: str
    organization: Optional[str] = None


class AgentResponse(BaseModel):
    """Response model for an agent."""
    agent_id: UUID
    name: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class ApiKeyRequest(BaseModel):
    """Request model for creating an API key."""
    name: str
    description: Optional[str] = None
    expires_in_days: Optional[int] = None
    permissions: Optional[List[str]] = None


class ApiKeyResponse(BaseModel):
    """Response model for an API key."""
    key_id: UUID
    api_key: str
    name: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes by default 