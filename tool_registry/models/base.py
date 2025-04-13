from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
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

Base = declarative_base(cls=Base) 