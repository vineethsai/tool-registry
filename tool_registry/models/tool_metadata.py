"""SQLAlchemy model for tool metadata in the Tool Registry system."""

from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base
from .base import UUIDType

class ToolMetadata(Base):
    """SQLAlchemy model for tool metadata in the Tool Registry system."""
    __tablename__ = 'tool_metadata'
    __table_args__ = {'extend_existing': True}

    metadata_id = Column(UUIDType(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUIDType(as_uuid=True), ForeignKey('tools.tool_id'), nullable=False)
    
    # Schema information
    schema_version = Column(String, nullable=False, default="1.0")
    schema_type = Column(String, nullable=False, default="openapi")
    schema_data = Column(JSON, nullable=False, default=dict)
    
    # Additional fields
    inputs = Column(JSON, nullable=False, default=dict)
    outputs = Column(JSON, nullable=False, default=dict)
    documentation_url = Column(String)
    provider = Column(String)
    tags = Column(JSON, nullable=False, default=list)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tool = relationship("Tool", back_populates="tool_metadata_rel")

    def __repr__(self):
        return f"<ToolMetadata for tool {self.tool_id} (version: {self.schema_version})>" 