"""SQLAlchemy model for access policies in the Tool Registry system."""

from datetime import datetime
import uuid
from uuid import UUID

from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PUUID
from sqlalchemy.orm import relationship

from ..core.database import Base
from .tool import tool_policy_association

class Policy(Base):
    """SQLAlchemy model for policies in the Tool Registry system."""
    
    __tablename__ = 'policies'
    __table_args__ = {'extend_existing': True}

    policy_id = Column(PUUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    rules = Column(JSON, nullable=False, default=dict())
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Foreign keys
    created_by = Column(PUUID(as_uuid=True), ForeignKey('agents.agent_id'), nullable=False)
    
    # Relationships
    creator = relationship("Agent", foreign_keys=[created_by])
    tools = relationship("Tool", secondary=tool_policy_association, back_populates="policies")
    access_logs = relationship("AccessLog", back_populates="policy", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Return string representation of the policy."""
        return f"<Policy(id={self.policy_id}, name='{self.name}')>" 