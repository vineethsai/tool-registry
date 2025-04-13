import json
from sqlalchemy import create_engine, Column, String, Boolean, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

# Custom JSON encoder
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

Base = declarative_base()

class ToolMetadata(Base):
    __tablename__ = "tool_metadata"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schema_version = Column(String, nullable=False, default="1.0")
    inputs = Column(JSON, nullable=False, default=dict)
    outputs = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Tool(Base):
    __tablename__ = "tools"
    
    tool_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    version = Column(String, nullable=False)
    tool_metadata_id = Column(UUID(as_uuid=True), ForeignKey("tool_metadata.id"), nullable=True)
    tool_metadata_json = Column(Text, nullable=False)  # Store as JSON string
    endpoint = Column(String, nullable=False)
    auth_required = Column(Boolean, default=False)
    auth_type = Column(String)
    auth_config = Column(Text)  # Store as JSON string
    rate_limit = Column(Integer)
    cost_per_call = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tool_metadata_rel = relationship("ToolMetadata", foreign_keys=[tool_metadata_id])
    
    @property
    def tool_metadata_dict(self):
        """Convert JSON string to dictionary"""
        if isinstance(self.tool_metadata_json, str):
            try:
                return json.loads(self.tool_metadata_json)
            except:
                return {}
        return self.tool_metadata_json
    
    @tool_metadata_dict.setter
    def tool_metadata_dict(self, value):
        """Convert dictionary to JSON string"""
        if isinstance(value, dict):
            self.tool_metadata_json = json.dumps(value, cls=DateTimeEncoder)
        else:
            self.tool_metadata_json = value

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    roles = Column(JSON, nullable=False, default=list)
    permissions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Credential(Base):
    __tablename__ = "credentials"
    
    credential_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.tool_id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    scopes = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", backref="credentials")
    tool = relationship("Tool", backref="credentials")

class Database:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def init_db(self):
        """Initialize the database by creating all tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close() 