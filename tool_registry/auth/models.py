from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class AgentCreate(BaseModel):
    """Model for creating a new agent."""
    name: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)

class AgentResponse(BaseModel):
    """Model for agent response."""
    id: UUID
    name: str
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    updated_at: datetime

class TokenResponse(BaseModel):
    """Model for token response."""
    access_token: str
    token_type: str

class SelfRegisterRequest(BaseModel):
    """Model for self-registration requests."""
    username: str
    email: EmailStr
    password: str
    name: str
    organization: Optional[str] = None

class ApiKeyRequest(BaseModel):
    """Model for API key generation."""
    name: str
    description: Optional[str] = None
    expires_in_days: Optional[int] = 30
    permissions: List[str] = Field(default_factory=list)

class ApiKeyResponse(BaseModel):
    """Model for API key response."""
    key_id: UUID
    api_key: str
    name: str
    expires_at: datetime
    created_at: datetime 