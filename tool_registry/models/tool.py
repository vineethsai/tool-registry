"""SQLAlchemy model for tools in the Tool Registry system."""

from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PUUID
import uuid

from ..core.database import Base

# Association table for tool-policy relationship
tool_policy_association = Table(
    'tool_policy_association',
    Base.metadata,
    Column('tool_id', PUUID(as_uuid=True), ForeignKey('tools.tool_id')),
    Column('policy_id', PUUID(as_uuid=True), ForeignKey('policies.policy_id')),
    extend_existing=True
)

class Tool(Base):
    """SQLAlchemy model for tools in the Tool Registry system."""
    __tablename__ = 'tools'
    __table_args__ = {'extend_existing': True}

    tool_id = Column(PUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    api_endpoint = Column(String, nullable=False)
    auth_method = Column(String, nullable=False)  # e.g., "API_KEY", "OAUTH2", "MTLS"
    auth_config = Column(JSON, nullable=False, default=dict())
    params = Column(JSON, nullable=False, default=dict())
    version = Column(String, nullable=False)
    tags = Column(JSON, nullable=False, default=list())
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
    allowed_scopes = Column(JSON, default=list())
    
    # Foreign keys
    owner_id = Column(PUUID(as_uuid=True), ForeignKey('agents.agent_id'), nullable=False)
    
    # Relationships
    owner = relationship("Agent", back_populates="owned_tools")
    policies = relationship("Policy", secondary=tool_policy_association, back_populates="tools")
    credentials = relationship("Credential", back_populates="tool", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="tool", cascade="all, delete-orphan")
    # Renamed to avoid conflict with SQLAlchemy's metadata attribute
    tool_metadata_rel = relationship("ToolMetadata", back_populates="tool", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Return string representation of the tool."""
        return f"<Tool(id={self.tool_id}, name='{self.name}', version='{self.version}')>" 