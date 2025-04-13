"""Pydantic models for tool metadata-related API requests and responses."""

from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List
from uuid import UUID
from datetime import datetime

class ToolMetadataCreate(BaseModel):
    """Request model for creating tool metadata."""
    schema_version: str = "1.0"
    schema_type: str = "openapi"
    schema_data: Dict[str, Any] = {}
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    documentation_url: Optional[str] = None
    provider: Optional[str] = None
    tags: List[str] = []

class ToolMetadataResponse(BaseModel):
    """Response model for tool metadata data."""
    metadata_id: UUID
    tool_id: UUID
    schema_version: str
    schema_type: str
    schema_data: Dict[str, Any]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    documentation_url: Optional[str] = None
    provider: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    # Alias for backward compatibility
    schema: Dict[str, Any] = Field(None, description="Deprecated, use schema_data instead")

    class Config:
        from_attributes = True 
        populate_by_name = True 