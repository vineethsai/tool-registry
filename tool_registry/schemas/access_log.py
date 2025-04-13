"""Pydantic models for access log-related API requests and responses."""

from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

class AccessLogCreate(BaseModel):
    """Request model for creating an access log entry."""
    agent_id: UUID
    tool_id: UUID
    credential_id: Optional[UUID] = None
    action: str
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class AccessLogResponse(BaseModel):
    """Response model for access log data."""
    log_id: UUID
    agent_id: UUID
    tool_id: UUID
    credential_id: Optional[UUID] = None
    timestamp: datetime
    action: str
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True 