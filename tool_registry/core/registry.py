"""Core registry functionality for managing tools and their metadata."""

from typing import Dict, List, Optional, Union, Any
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid

from ..models.tool import Tool as DBTool
from ..models.tool_metadata import ToolMetadata as DBToolMetadata
from .database import Database

class ToolRegistry:
    """Registry for managing tools and their metadata."""
    
    def __init__(self, db: Union[Session, Database]):
        """Initialize the tool registry with a database session."""
        if isinstance(db, Database):
            # Get a session from the Database object
            self.db_instance = db
            self.db = next(db.get_session())
        else:
            # Use the provided session directly
            self.db_instance = None
            self.db = db
        self.tools = {}  # For backward compatibility
        self._metadata: Dict[UUID, DBToolMetadata] = {}

    async def register_tool(self, tool_data: Union[Dict[str, Any], DBTool]) -> Dict[str, Any]:
        """Register a new tool in the registry."""
        if isinstance(tool_data, DBTool):
            # If we received a Tool object, extract the relevant fields
            tool_dict = {
                "name": tool_data.name,
                "description": tool_data.description,
                "api_endpoint": tool_data.api_endpoint,
                "auth_method": tool_data.auth_method,
                "auth_config": tool_data.auth_config,
                "params": tool_data.params,
                "version": tool_data.version,
                "tags": tool_data.tags,
                "owner_id": tool_data.owner_id,
                "tool_id": tool_data.tool_id
            }
            # Use the existing tool_id if provided
            tool_id = tool_data.tool_id
        else:
            # Using dictionary input
            tool_dict = tool_data
            tool_id = uuid.uuid4()
            
        # Check if tool with the same name exists
        existing_tool = self.db.query(DBTool).filter(DBTool.name == tool_dict["name"]).first()
        if existing_tool:
            raise ValueError(f"Tool with name '{tool_dict['name']}' already exists")
        
        # Create tool in database
        new_tool = DBTool(
            tool_id=tool_id,
            name=tool_dict["name"],
            description=tool_dict.get("description", ""),
            api_endpoint=tool_dict.get("api_endpoint", ""),
            auth_method=tool_dict.get("auth_method", ""),
            auth_config=tool_dict.get("auth_config", {}),
            params=tool_dict.get("params", {}),
            version=tool_dict.get("version", "1.0.0"),
            tags=tool_dict.get("tags", []),
            owner_id=tool_dict.get("owner_id"),
        )
        self.db.add(new_tool)
        self.db.commit()
        self.db.refresh(new_tool)
        
        # For backward compatibility
        self.tools[tool_id] = tool_dict
        
        return tool_id

    async def get_tool(self, tool_id: Union[str, UUID]) -> Optional[DBTool]:
        """Get a tool by ID."""
        if isinstance(tool_id, str):
            tool_id = UUID(tool_id)
            
        tool = self.db.query(DBTool).filter(DBTool.tool_id == tool_id).first()
        return tool

    async def list_tools(self) -> List[DBTool]:
        """List all registered tools."""
        tools = self.db.query(DBTool).all()
        return tools

    async def search_tools(self, query: str) -> List[DBTool]:
        """
        Search for tools by name, description, or tags.
        
        Args:
            query: The search query to filter tools
            
        Returns:
            List of tools matching the query
        """
        query = query.lower()
        
        # Perform SQL query to filter tools based on name and description
        # For tags, we'll filter in Python since JSON searching in SQLite is limited
        tools = self.db.query(DBTool).filter(
            or_(
                DBTool.name.ilike(f"%{query}%"),
                DBTool.description.ilike(f"%{query}%")
            )
        ).all()
        
        # Filter by tags in Python
        # Get all tools that weren't already matched
        all_tools = self.db.query(DBTool).all()
        matched_ids = {tool.tool_id for tool in tools}
        
        # Look for tag matches
        for tool in all_tools:
            if tool.tool_id in matched_ids:
                continue
                
            # Check if any tag contains the query
            if tool.tags and any(query in tag.lower() for tag in tool.tags):
                tools.append(tool)
        
        return tools

    async def update_tool(self, tool_id: Union[str, UUID], updated_data: Union[Dict[str, Any], DBTool]) -> bool:
        """Update a tool's metadata."""
        if isinstance(tool_id, str):
            tool_id = UUID(tool_id)
            
        tool = self.db.query(DBTool).filter(DBTool.tool_id == tool_id).first()
        if not tool:
            raise ValueError(f"Tool with ID {tool_id} not found")
        
        if isinstance(updated_data, DBTool):
            # If we received a Tool object, extract the relevant fields
            update_dict = {
                "name": updated_data.name,
                "description": updated_data.description,
                "api_endpoint": updated_data.api_endpoint,
                "auth_method": updated_data.auth_method,
                "auth_config": updated_data.auth_config,
                "params": updated_data.params,
                "version": updated_data.version,
                "tags": updated_data.tags,
            }
        else:
            update_dict = updated_data
            
        # Update tool fields
        for key, value in update_dict.items():
            if hasattr(tool, key) and value is not None:
                setattr(tool, key, value)
                
        self.db.commit()
        self.db.refresh(tool)
        
        # For backward compatibility
        if tool_id in self.tools:
            self.tools[tool_id].update(update_dict)
            
        return True

    async def delete_tool(self, tool_id: Union[str, UUID]) -> bool:
        """Delete a tool from the registry."""
        if isinstance(tool_id, str):
            tool_id = UUID(tool_id)
            
        tool = self.db.query(DBTool).filter(DBTool.tool_id == tool_id).first()
        if not tool:
            return False
            
        self.db.delete(tool)
        self.db.commit()
        
        # For backward compatibility
        if tool_id in self.tools:
            del self.tools[tool_id]
            
        return True
        
    def __del__(self):
        """Clean up resources."""
        if self.db_instance is not None:
            self.db.close() 