"""SQLAlchemy model for credentials in the Tool Registry system."""

from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PUUID

from ..core.database import Base

class Credential(Base):
    """SQLAlchemy model for credentials in the Tool Registry system."""
    __tablename__ = 'credentials'
    __table_args__ = {'extend_existing': True}

    credential_id = Column(PUUID(as_uuid=True), primary_key=True)
    token = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Foreign keys
    agent_id = Column(PUUID(as_uuid=True), ForeignKey('agents.agent_id'), nullable=False)
    tool_id = Column(PUUID(as_uuid=True), ForeignKey('tools.tool_id'), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="credentials")
    tool = relationship("Tool", back_populates="credentials")
    access_logs = relationship("AccessLog", back_populates="credential", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Credential(id={self.credential_id}, agent='{self.agent_id}', tool='{self.tool_id}')>"

    @property
    def is_expired(self) -> bool:
        """Check if the credential has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the credential is valid (not expired and not revoked)."""
        return not (self.is_expired or self.is_revoked) 