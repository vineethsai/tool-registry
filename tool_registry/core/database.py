"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import json
from uuid import UUID
from typing import Generator

# Custom JSON serializer for handling UUIDs
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # Convert UUID to string
            return str(obj)
        return super().default(obj)

# Configure SQLAlchemy to use our custom JSON encoder for all JSON columns
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from sqlalchemy import JSON as SA_JSON

# Override the JSON serializer
PG_JSON.serializer = lambda obj: json.dumps(obj, cls=UUIDEncoder)
SA_JSON.serializer = lambda obj: json.dumps(obj, cls=UUIDEncoder)

# Create base class for models
Base = declarative_base()

class Database:
    """Database management class for the Tool Registry system."""
    
    def __init__(self, database_url: str = "sqlite:///./tool_registry.db"):
        """Initialize the database with the given URL."""
        self.database_url = database_url
        
        # Set connection arguments based on database type
        connect_args = {}
        if database_url.startswith('sqlite'):
            # SQLite-specific connection args
            connect_args = {"check_same_thread": False}
            
        self.engine = create_engine(
            database_url,
            connect_args=connect_args,
            poolclass=StaticPool if database_url.startswith('sqlite') else None
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    def init_db(self):
        """Initialize the database by creating all tables."""
        Base.metadata.create_all(bind=self.engine)

# Create default database instance
database = Database()
engine = database.engine
SessionLocal = database.SessionLocal

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    """Provide a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize tables
Base.metadata.create_all(bind=engine)

__all__ = ['Base', 'engine', 'SessionLocal', 'get_db', 'Database'] 