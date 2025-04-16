"""Pydantic models for tool metadata-related API requests and responses."""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Any, List, Union
from uuid import UUID
from datetime import datetime
import json

class ToolMetadataCreate(BaseModel):
    """Request model for creating tool metadata."""
    schema_version: str = Field("1.0", description="Version of the schema format", example="1.0")
    schema_type: str = Field("openapi", description="Type of schema (openapi, jsonschema, etc.)", example="openapi")
    schema_data: Dict[str, Any] = Field({}, description="Complete schema definition in the specified format")
    inputs: Dict[str, Any] = Field({}, description="Input parameter definitions", example={"text": {"type": "string", "description": "Input text to process"}})
    outputs: Dict[str, Any] = Field({}, description="Output format definitions", example={"result": {"type": "string", "description": "Processed result"}})
    documentation_url: Optional[str] = Field(None, description="URL to the tool's documentation", example="https://docs.example.com/tool")
    provider: Optional[str] = Field(None, description="Provider or creator of the tool", example="Example Corp")
    tags: List[str] = Field([], description="Additional tags for categorizing the tool metadata", example=["nlp", "processing"])

class ToolMetadataResponse(BaseModel):
    """Response model for tool metadata data."""
    metadata_id: UUID = Field(..., description="Unique identifier for the metadata")
    tool_id: UUID = Field(..., description="ID of the tool this metadata belongs to")
    schema_version: str = Field(..., description="Version of the schema format")
    schema_type: str = Field(..., description="Type of schema (openapi, jsonschema, etc.)")
    schema_data: Union[Dict[str, Any], str] = Field(..., description="Complete schema definition in the specified format")
    inputs: Dict[str, Any] = Field(..., description="Input parameter definitions")
    outputs: Dict[str, Any] = Field(..., description="Output format definitions")
    documentation_url: Optional[str] = Field(None, description="URL to the tool's documentation")
    provider: Optional[str] = Field(None, description="Provider or creator of the tool")
    tags: List[str] = Field([], description="Additional tags for categorizing the tool metadata")
    created_at: datetime = Field(..., description="Timestamp when the metadata was created")
    updated_at: datetime = Field(..., description="Timestamp when the metadata was last updated")

    # Alias for backward compatibility
    schema: Dict[str, Any] = Field(None, description="Deprecated, use schema_data instead")

    @field_validator('schema_data')
    @classmethod
    def validate_schema_data(cls, v):
        """Convert schema_data from string to dict if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"raw_data": v}
        return v

    @field_validator('inputs', 'outputs', mode='before')
    @classmethod
    def ensure_dict(cls, v):
        """Ensure inputs and outputs are dictionaries."""
        if v is None:
            return {}
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    class Config:
        from_attributes = True 
        populate_by_name = True 