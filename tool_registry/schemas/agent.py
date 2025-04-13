"""Pydantic models for agent-related API requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class AgentCreate(BaseModel):
    """Schema for creating a new agent."""
    name: str = Field(..., description="Name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    creator: Optional[UUID] = Field(None, description="ID of the agent creating this agent")
    is_admin: bool = Field(False, description="Whether the agent has admin privileges")
    roles: List[str] = []

class AgentUpdate(BaseModel):
    """Request model for updating an existing agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    roles: Optional[List[str]] = None
    allowed_tools: Optional[List[UUID]] = None

class AgentResponse(BaseModel):
    """Schema for agent response."""
    agent_id: UUID
    name: str
    description: Optional[str]
    creator: Optional[UUID]
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    roles: List[str]
    allowed_tools: List[UUID] = []
    request_count: int = 0

    class Config:
        orm_mode = True 