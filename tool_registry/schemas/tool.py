"""Pydantic models for tool-related API requests and responses."""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime

from .tool_metadata import ToolMetadataResponse

class ToolBase(BaseModel):
    """Base model with common tool fields."""
    name: str
    description: Optional[str] = None
    api_endpoint: str = Field(..., description="The API endpoint for the tool")
    auth_method: str
    auth_config: Dict[str, Any] = {}
    params: Dict[str, Any] = {}
    version: str
    tags: List[str] = []
    allowed_scopes: List[str] = ["read"]

class ToolCreate(ToolBase):
    """Request model for creating a new tool."""
    owner_id: Optional[UUID] = None
    
class ToolUpdate(BaseModel):
    """Request model for updating an existing tool."""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    api_endpoint: Optional[str] = Field(None, description="The API endpoint for the tool")
    auth_method: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    allowed_scopes: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ToolResponse(BaseModel):
    """Response model for tool data."""
    tool_id: UUID
    name: str
    description: Optional[str] = None
    api_endpoint: str = Field(..., description="The API endpoint for the tool")
    auth_method: str
    auth_config: Dict[str, Any] = {}
    params: Dict[str, Any] = {}
    version: str
    tags: List[str] = []
    allowed_scopes: List[str] = ["read"]
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Optional[ToolMetadataResponse] = None

    class Config:
        from_attributes = True
        populate_by_name = True
        
        @classmethod
        def _get_value(cls, v, field, *args, **kwargs):
            """Custom getter to handle field aliases and attribute names."""
            if isinstance(v, dict):
                # For endpoint/api_endpoint mismatch
                if "endpoint" in v and field.name == "api_endpoint":
                    return v.get("endpoint")
                # For tool_metadata_rel/metadata mismatch
                if "tool_metadata_rel" in v and field.name == "metadata":
                    return v.get("tool_metadata_rel")
            return v 