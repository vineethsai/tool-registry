"""Pydantic models for credential-related API requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

class CredentialCreate(BaseModel):
    """Request model for creating a credential."""
    tool_id: UUID = Field(..., description="ID of the tool to generate credentials for")
    scope: Optional[List[str]] = Field([], description="Requested permission scopes for the tool", example=["read", "write"])
    duration: Optional[timedelta] = Field(timedelta(minutes=30), description="Duration for which the credential is valid")
    context: Optional[Dict[str, Any]] = Field({}, description="Additional context information for the credential")

class CredentialResponse(BaseModel):
    """Response model for credential data."""
    credential_id: UUID = Field(..., description="Unique identifier for the credential")
    agent_id: UUID = Field(..., description="ID of the agent the credential is issued to")
    tool_id: UUID = Field(..., description="ID of the tool the credential grants access to")
    token: str = Field(..., description="The credential token to use for authentication")
    expires_at: datetime = Field(..., description="Timestamp when the credential expires")
    created_at: datetime = Field(..., description="Timestamp when the credential was created")
    scope: List[str] = Field(..., description="Permission scopes granted by this credential")
    context: Dict[str, Any] = Field({}, description="Additional context information for the credential")

    class Config:
        from_attributes = True 