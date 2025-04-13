"""SQLAlchemy model for agents in the Tool Registry system."""

from datetime import datetime
import uuid
from uuid import UUID

from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base
from .base import UUIDType

class Agent(Base):
    """SQLAlchemy model for agents in the Tool Registry system."""
    
    __tablename__ = 'agents'
    __table_args__ = {'extend_existing': True}

    agent_id = Column(UUIDType(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    roles = Column(JSON, nullable=False, default=list())  # List of role names
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator = Column(UUIDType(as_uuid=True), ForeignKey('agents.agent_id'), nullable=True)
    api_key_hash = Column(String)  # Stored hash of API key for authentication
    allowed_tools = Column(JSON, default=list())  # List of tool IDs this agent can access
    request_count = Column(Integer, nullable=False, default=0)  # Number of requests made by this agent
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    created_by = relationship("Agent", remote_side=[agent_id])
    owned_tools = relationship("Tool", back_populates="owner", cascade="all, delete-orphan")
    created_policies = relationship("Policy", back_populates="creator")
    credentials = relationship("Credential", back_populates="agent", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Return string representation of the agent."""
        return f"<Agent(id={self.agent_id}, name='{self.name}', admin={self.is_admin})>"

    @property
    def is_admin(self) -> bool:
        """Check if the agent has admin role."""
        return "admin" in (self.roles or []) 