"""SQLAlchemy model for access logs in the Tool Registry system."""

from uuid import UUID
from datetime import datetime
import uuid
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..core.database import Base
from .base import UUIDType

class AccessLog(Base):
    """SQLAlchemy model for access logs in the Tool Registry system."""
    __tablename__ = 'access_logs'
    __table_args__ = {'extend_existing': True}

    log_id = Column(UUIDType(as_uuid=True), primary_key=True, default=uuid.uuid4)
    access_granted = Column(Boolean, nullable=False)
    reason = Column(String)
    request_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign keys
    agent_id = Column(UUIDType(as_uuid=True), ForeignKey('agents.agent_id'), nullable=False)
    tool_id = Column(UUIDType(as_uuid=True), ForeignKey('tools.tool_id'), nullable=False)
    policy_id = Column(UUIDType(as_uuid=True), ForeignKey('policies.policy_id'), nullable=True)
    credential_id = Column(UUIDType(as_uuid=True), ForeignKey('credentials.credential_id'), nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="access_logs")
    tool = relationship("Tool", back_populates="access_logs")
    policy = relationship("Policy", back_populates="access_logs")
    credential = relationship("Credential", back_populates="access_logs")

    def __repr__(self):
        return f"<AccessLog(id={self.log_id}, agent='{self.agent_id}', tool='{self.tool_id}', granted={self.access_granted})>" 