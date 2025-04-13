"""Pydantic models for tool-related API requests and responses."""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime

from .tool_metadata import ToolMetadataResponse

class ToolBase(BaseModel):
    """Base model with common tool fields."""
    name: str = Field(..., description="Unique name of the tool", example="text-translator")
    description: Optional[str] = Field(None, description="Detailed description of the tool's functionality", example="Translates text between languages")
    api_endpoint: str = Field(..., description="The API endpoint URL for the tool", example="https://api.example.com/tools/translate")
    auth_method: str = Field(..., description="Authentication method required for the tool (API_KEY, OAUTH, JWT)", example="API_KEY")
    auth_config: Dict[str, Any] = Field({}, description="Configuration for the authentication method")
    params: Dict[str, Any] = Field({}, description="Parameters for the tool")
    version: str = Field(..., description="Version of the tool (semantic versioning recommended)", example="1.0.0")
    tags: List[str] = Field([], description="Tags for categorizing the tool", example=["translation", "language", "text"])
    allowed_scopes: List[str] = Field(["read"], description="Allowed scopes for accessing the tool", example=["read", "write"])

class ToolCreate(ToolBase):
    """Request model for creating a new tool."""
    owner_id: Optional[UUID] = None
    
class ToolUpdate(BaseModel):
    """Request model for updating an existing tool."""
    name: Optional[str] = Field(None, description="Updated name of the tool")
    description: Optional[str] = Field(None, description="Updated description of the tool")
    version: Optional[str] = Field(None, description="Updated version of the tool")
    api_endpoint: Optional[str] = Field(None, description="Updated API endpoint for the tool")
    auth_method: Optional[str] = Field(None, description="Updated authentication method")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Updated authentication configuration")
    params: Optional[Dict[str, Any]] = Field(None, description="Updated parameters for the tool")
    tags: Optional[List[str]] = Field(None, description="Updated tags for categorizing the tool")
    allowed_scopes: Optional[List[str]] = Field(None, description="Updated allowed scopes for the tool")
    is_active: Optional[bool] = Field(None, description="Whether the tool is active and available for use")

class ToolResponse(BaseModel):
    """Response model for tool data."""
    tool_id: UUID = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Name of the tool")
    description: Optional[str] = Field(None, description="Description of the tool")
    api_endpoint: str = Field(..., description="The API endpoint for the tool")
    auth_method: str = Field(..., description="Authentication method required (API_KEY, OAUTH, JWT)")
    auth_config: Dict[str, Any] = Field({}, description="Configuration for the authentication method")
    params: Dict[str, Any] = Field({}, description="Parameters for the tool")
    version: str = Field(..., description="Version of the tool")
    tags: List[str] = Field([], description="Tags for categorizing the tool")
    allowed_scopes: List[str] = Field(["read"], description="Allowed scopes for accessing the tool")
    owner_id: UUID = Field(..., description="ID of the agent who owns/created this tool")
    created_at: datetime = Field(..., description="Timestamp when the tool was created")
    updated_at: datetime = Field(..., description="Timestamp when the tool was last updated")
    is_active: bool = Field(True, description="Whether the tool is active and available for use")
    metadata: Optional[ToolMetadataResponse] = Field(None, description="Additional metadata about the tool")

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