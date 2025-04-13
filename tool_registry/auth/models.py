from pydantic import BaseModel, Field
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