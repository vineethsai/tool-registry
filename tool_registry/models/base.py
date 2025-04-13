"""Base models and types for SQLAlchemy models."""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PUUID
from sqlalchemy import TypeDecorator, String
from uuid import UUID
import json
from uuid import UUID as _UUID

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, _UUID):
            return str(obj)
        return super().default(obj)

class Base:
    """Base class for all SQLAlchemy models."""
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def to_json(self):
        """Convert model instance to JSON string."""
        return json.dumps(self.to_dict(), cls=UUIDEncoder)

class UUIDType(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses String(36).
    """
    impl = String
    cache_ok = True

    def __init__(self, as_uuid=True):
        self.as_uuid = as_uuid
        super().__init__(36)
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PUUID(as_uuid=self.as_uuid))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, UUID):
                return str(value)
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if self.as_uuid:
            if isinstance(value, UUID):
                return value
            try:
                return UUID(value)
            except (TypeError, AttributeError):
                # Handle the case where value might be an integer
                return value
        return value

Base = declarative_base(cls=Base) 