"""Core registry functionality for managing tools and their metadata."""

from typing import Dict, List, Optional, Union, Any
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, text, func
import uuid
import logging

from ..models.tool import Tool as DBTool
from ..models.tool_metadata import ToolMetadata as DBToolMetadata
from .database import Database

# Initialize logger for this module
logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry for managing tools and their metadata."""
    
    def __init__(self, db: Union[Session, Database]):
        """Initialize the tool registry with a database session."""
        if isinstance(db, Database):
            # Get a session from the Database object
            self.db_instance = db
            self.db = next(db.get_session())
            logger.debug("Initialized ToolRegistry with Database instance")
        else:
            # Use the provided session directly
            self.db_instance = None
            self.db = db
            logger.debug("Initialized ToolRegistry with Session instance")
        self.tools = {}  # For backward compatibility
        self._tools = {}  # Add this attribute to fix the error
        self._metadata: Dict[UUID, DBToolMetadata] = {}
        logger.info("ToolRegistry initialized")

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
            logger.debug(f"Registering existing tool with ID: {tool_id}")
        else:
            # Using dictionary input
            tool_dict = tool_data
            tool_id = uuid.uuid4()
            logger.debug(f"Registering new tool with generated ID: {tool_id}")
            
        # Check if tool with the same name exists
        existing_tool = self.db.query(DBTool).filter(DBTool.name == tool_dict["name"]).first()
        if existing_tool:
            logger.warning(f"Tool registration failed: Tool with name '{tool_dict['name']}' already exists")
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
        
        logger.info(f"Tool registered successfully: {new_tool.name} (ID: {new_tool.tool_id})")
        logger.debug(f"Tool details: API endpoint: {new_tool.api_endpoint}, Version: {new_tool.version}, Tags: {new_tool.tags}")
        
        # For backward compatibility
        self.tools[tool_id] = tool_dict
        
        return tool_id

    async def get_tool(self, tool_id: Union[str, UUID]) -> Optional[DBTool]:
        """Get a tool by ID."""
        try:
            if isinstance(tool_id, str):
                tool_id = UUID(tool_id)
            
            logger.debug(f"Getting tool with ID: {tool_id}")    
            tool = self.db.query(DBTool).filter(DBTool.tool_id == tool_id).first()
            
            if tool:
                logger.debug(f"Found tool: {tool.name}")
            else:
                logger.debug(f"Tool not found with ID: {tool_id}")
                
            return tool
        except ValueError as e:
            logger.error(f"Invalid UUID format for tool_id: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving tool: {str(e)}")
            return None

    async def list_tools(self) -> List[DBTool]:
        """List all registered tools."""
        try:
            logger.debug("Listing all tools")
            tools = self.db.query(DBTool).all()
            logger.info(f"Retrieved {len(tools)} tools from registry")
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            return []

    async def search_tools(self, query: str) -> List[DBTool]:
        """
        Search for tools by name, description, or tags.
        
        Args:
            query: The search string
            
        Returns:
            List of matching tools
        """
        try:
            logger.debug(f"Searching tools for: {query}")
            query_lower = query.lower()
            
            # First try to get results from the database
            tools = self.db.query(DBTool).filter(
                or_(
                    func.lower(DBTool.name).contains(query_lower),
                    func.lower(DBTool.description).contains(query_lower)
                )
            ).all()
            
            # Also search through tags
            tag_matched_tools = self.db.query(DBTool).all()
            tag_results = [
                tool for tool in tag_matched_tools 
                if tool.tags and any(query_lower in tag.lower() for tag in tool.tags)
            ]
            
            # Combine results, ensuring no duplicates
            all_results = {str(tool.tool_id): tool for tool in tools}
            for tool in tag_results:
                all_results[str(tool.tool_id)] = tool
                
            logger.info(f"Found {len(all_results)} tools matching '{query}'")
            return list(all_results.values())
        except Exception as e:
            logger.error(f"Error searching tools: {str(e)}")
            return []

    async def update_tool(self, tool_id: Union[str, UUID], updated_data: Union[Dict[str, Any], DBTool]) -> bool:
        """Update a tool's metadata."""
        if isinstance(tool_id, str):
            tool_id = UUID(tool_id)
        
        logger.info(f"Updating tool with ID: {tool_id}")
            
        tool = self.db.query(DBTool).filter(DBTool.tool_id == tool_id).first()
        if not tool:
            logger.warning(f"Tool update failed: Tool with ID {tool_id} not found")
            raise ValueError(f"Tool with ID {tool_id} not found")
        
        logger.debug(f"Found tool to update: {tool.name}")
        
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
        
        logger.debug(f"Update fields: {list(update_dict.keys())}")
            
        # Update tool fields
        for key, value in update_dict.items():
            if hasattr(tool, key) and value is not None:
                setattr(tool, key, value)
                
        self.db.commit()
        self.db.refresh(tool)
        
        logger.info(f"Tool updated successfully: {tool.name} (ID: {tool.tool_id})")
        
        # For backward compatibility
        if tool_id in self.tools:
            self.tools[tool_id].update(update_dict)
            
        return True

    async def delete_tool(self, tool_id: Union[str, UUID]) -> bool:
        """Delete a tool from the registry."""
        if isinstance(tool_id, str):
            tool_id = UUID(tool_id)
        
        logger.info(f"Deleting tool with ID: {tool_id}")
            
        tool = self.db.query(DBTool).filter(DBTool.tool_id == tool_id).first()
        if not tool:
            logger.warning(f"Tool deletion failed: Tool with ID {tool_id} not found")
            return False
        
        tool_name = tool.name
        self.db.delete(tool)
        self.db.commit()
        
        logger.info(f"Tool deleted successfully: {tool_name} (ID: {tool_id})")
        
        # For backward compatibility
        if tool_id in self.tools:
            del self.tools[tool_id]
            
        return True
        
    def __del__(self):
        """Clean up resources."""
        if self.db_instance is not None:
            logger.debug("Closing database session in ToolRegistry destructor")
            self.db.close() 