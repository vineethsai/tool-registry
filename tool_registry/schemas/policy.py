"""Pydantic models for policy-related API requests and responses."""

from pydantic import BaseModel
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime

class PolicyCreate(BaseModel):
    """Request model for creating a new policy."""
    name: str
    description: str
    tool_id: Optional[UUID] = None
    allowed_scopes: List[str] = []
    conditions: Dict = {}
    rules: Dict = {}  # New field for storing policy rules
    priority: int = 0
    is_active: bool = True

class PolicyUpdate(BaseModel):
    """Request model for updating an existing policy."""
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_scopes: Optional[List[str]] = None
    conditions: Optional[Dict] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class PolicyResponse(BaseModel):
    """Response model for policy data."""
    policy_id: UUID
    name: str
    description: str
    tool_id: Optional[UUID]
    allowed_scopes: List[str]
    conditions: Dict
    rules: Dict = {}  # New field for storing policy rules
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True 