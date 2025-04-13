"""Pydantic models for credential-related API requests and responses."""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

class CredentialCreate(BaseModel):
    """Request model for creating a credential."""
    tool_id: UUID
    scope: Optional[List[str]] = []
    duration: Optional[timedelta] = timedelta(minutes=30)
    context: Optional[Dict[str, Any]] = {}

class CredentialResponse(BaseModel):
    """Response model for credential data."""
    credential_id: UUID
    agent_id: UUID
    tool_id: UUID
    token: str
    expires_at: datetime
    created_at: datetime
    scope: List[str]
    context: Dict[str, Any]

    class Config:
        from_attributes = True 