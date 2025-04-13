from typing import Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from datetime import datetime
from .database import Database, Tool as DBTool

class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""
    schema_version: str = "1.0"
    inputs: Dict[str, Dict[str, str]]
    outputs: Dict[str, Dict[str, str]]

class Tool(BaseModel):
    """A tool in the registry."""
    tool_id: UUID
    name: str
    description: str
    version: str
    tool_metadata_rel: ToolMetadata
    endpoint: str
    auth_required: bool = False
    auth_type: Optional[str] = None
    auth_config: Optional[Dict] = None
    rate_limit: Optional[int] = None
    cost_per_call: Optional[float] = None

class ToolRegistry:
    """Core registry for managing tools."""
    
    def __init__(self, db: Database):
        """Initialize the tool registry."""
        self.db = db
    
    async def register_tool(self, tool: Tool) -> UUID:
        """Register a new tool in the registry."""
        session = next(self.db.get_session())
        try:
            # Check for existing tool with the same name
            existing_tool = session.query(DBTool).filter(DBTool.name == tool.name).first()
            if existing_tool:
                raise ValueError(f"Tool with name {tool.name} already exists")
            
            db_tool = DBTool(
                tool_id=tool.tool_id,
                name=tool.name,
                description=tool.description,
                version=tool.version,
                endpoint=tool.endpoint,
                auth_required=tool.auth_required,
                auth_type=tool.auth_type,
                rate_limit=tool.rate_limit,
                cost_per_call=tool.cost_per_call
            )
            db_tool.tool_metadata_dict = tool.tool_metadata_rel.model_dump()
            session.add(db_tool)
            session.commit()
            return db_tool.tool_id
        finally:
            session.close()
    
    async def get_tool(self, tool_id: UUID) -> Optional[Tool]:
        """Get a tool by its ID."""
        session = next(self.db.get_session())
        try:
            db_tool = session.query(DBTool).filter(DBTool.tool_id == tool_id).first()
            if db_tool:
                return Tool(
                    tool_id=db_tool.tool_id,
                    name=db_tool.name,
                    description=db_tool.description,
                    version=db_tool.version,
                    tool_metadata_rel=ToolMetadata(**db_tool.tool_metadata_dict),
                    endpoint=db_tool.endpoint,
                    auth_required=db_tool.auth_required,
                    auth_type=db_tool.auth_type,
                    rate_limit=db_tool.rate_limit,
                    cost_per_call=db_tool.cost_per_call
                )
            return None
        finally:
            session.close()
    
    async def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Get a tool by its name."""
        session = next(self.db.get_session())
        try:
            # Since name is now a direct field in the DBTool model
            db_tool = session.query(DBTool).filter(DBTool.name == name).first()
            
            if db_tool:
                return Tool(
                    tool_id=db_tool.tool_id,
                    name=db_tool.name,
                    description=db_tool.description,
                    version=db_tool.version,
                    tool_metadata_rel=ToolMetadata(**db_tool.tool_metadata_dict),
                    endpoint=db_tool.endpoint,
                    auth_required=db_tool.auth_required,
                    auth_type=db_tool.auth_type,
                    rate_limit=db_tool.rate_limit,
                    cost_per_call=db_tool.cost_per_call
                )
            return None
        finally:
            session.close()
    
    async def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        session = next(self.db.get_session())
        try:
            db_tools = session.query(DBTool).all()
            return [
                Tool(
                    tool_id=db_tool.tool_id,
                    name=db_tool.name,
                    description=db_tool.description,
                    version=db_tool.version,
                    tool_metadata_rel=ToolMetadata(**db_tool.tool_metadata_dict),
                    endpoint=db_tool.endpoint,
                    auth_required=db_tool.auth_required,
                    auth_type=db_tool.auth_type,
                    rate_limit=db_tool.rate_limit,
                    cost_per_call=db_tool.cost_per_call
                )
                for db_tool in db_tools
            ]
        finally:
            session.close()
    
    async def search_tools(self, query: str) -> List[Tool]:
        """Search tools by name, description."""
        session = next(self.db.get_session())
        try:
            # Search by name and description fields directly
            db_tools = session.query(DBTool).filter(
                (DBTool.name.ilike(f"%{query}%")) |
                (DBTool.description.ilike(f"%{query}%"))
            ).all()
            
            return [
                Tool(
                    tool_id=db_tool.tool_id,
                    name=db_tool.name,
                    description=db_tool.description,
                    version=db_tool.version,
                    tool_metadata_rel=ToolMetadata(**db_tool.tool_metadata_dict),
                    endpoint=db_tool.endpoint,
                    auth_required=db_tool.auth_required,
                    auth_type=db_tool.auth_type,
                    rate_limit=db_tool.rate_limit,
                    cost_per_call=db_tool.cost_per_call
                )
                for db_tool in db_tools
            ]
        finally:
            session.close()
    
    async def update_tool(self, tool_id: UUID, tool: Tool) -> bool:
        """Update a tool in the registry."""
        session = next(self.db.get_session())
        try:
            db_tool = session.query(DBTool).filter(DBTool.tool_id == tool_id).first()
            if not db_tool:
                return False

            # Update the name, description, and version
            db_tool.name = tool.name
            db_tool.description = tool.description
            db_tool.version = tool.version
            
            # Update the tool_metadata_json field
            db_tool.tool_metadata_dict = tool.tool_metadata_rel.model_dump()
            
            # Update other fields
            db_tool.endpoint = tool.endpoint
            db_tool.auth_required = tool.auth_required
            db_tool.auth_type = tool.auth_type
            db_tool.auth_config = None if tool.auth_config is None else str(tool.auth_config)
            db_tool.rate_limit = tool.rate_limit
            db_tool.cost_per_call = tool.cost_per_call

            session.commit()
            return True
        finally:
            session.close()
    
    async def delete_tool(self, tool_id: UUID) -> bool:
        """Delete a tool from the registry."""
        session = next(self.db.get_session())
        try:
            db_tool = session.query(DBTool).filter(DBTool.tool_id == tool_id).first()
            if not db_tool:
                return False

            session.delete(db_tool)
            session.commit()
            return True
        finally:
            session.close() 