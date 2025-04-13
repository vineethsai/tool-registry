"""
Example usage of the GenAI Tool Registry system.

This script demonstrates how to:
1. Initialize the services
2. Create an agent
3. Register a tool
4. Generate credentials
"""
import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from tool_registry.core.database import Database
from tool_registry.core.registry import ToolRegistry
from tool_registry.auth.service import AuthService
from tool_registry.core.credentials import CredentialVendor
from tool_registry.models.tool import Tool
from tool_registry.models.tool_metadata import ToolMetadata

async def main():
    # Initialize the database
    db = Database("sqlite:///./example.db")
    db.init_db()
    
    # Initialize services
    auth_service = AuthService(db)
    registry = ToolRegistry(db)
    credential_vendor = CredentialVendor()

    # Create an agent with specific roles and permissions
    agent_data = {
        "name": "example-agent",
        "role": "developer",
        "permissions": ["tool:read", "tool:write"]
    }
    agent_id = await auth_service.create_agent(agent_data)
    print(f"Created agent with ID: {agent_id}")

    # Define tool metadata
    tool_metadata = ToolMetadata(
        usage_count=0,
        last_used=datetime.utcnow(),
        average_latency=0,
        error_rate=0,
        custom_metrics={"key": "value"}
    )
    
    # Register a tool with the registry
    tool_data = {
        "name": "example-tool",
        "description": "An example tool for demonstration",
        "api_endpoint": "https://api.example.com/v1/example-tool",
        "auth_method": "api_key",
        "auth_config": {"header_name": "X-API-Key"},
        "params": {"param1": "string", "param2": "integer"},
        "version": "1.0.0",
        "tags": ["example", "demo"],
        "allowed_scopes": ["read", "write"],
        "owner_id": agent_id
    }
    
    # Create the tool with its metadata
    session = next(db.get_session())
    try:
        tool = Tool(**tool_data)
        tool.tool_metadata_rel = tool_metadata  # Note the use of tool_metadata_rel
        session.add(tool)
        session.commit()
        tool_id = tool.tool_id
        print(f"Registered tool with ID: {tool_id}")
    finally:
        session.close()
    
    # Alternative: use the registry service
    # tool_id = await registry.register_tool(tool_data)
    # print(f"Registered tool with ID: {tool_id}")
    
    # Generate credentials for the agent to access the tool
    credential = credential_vendor.generate_credential(
        agent_id=agent_id,
        tool_id=tool_id,
        duration=timedelta(hours=1),
        scopes=["read"]
    )
    print(f"Generated credential: {credential.token}")
    
    # Validate the credential
    validated = credential_vendor.validate_credential(credential.token)
    print(f"Credential is valid: {validated is not None}")
    
    # Search for tools
    tools = await registry.search_tools("example")
    print(f"Found {len(tools)} tools matching 'example'")
    
    # Update a tool
    updated_data = {"description": "Updated example tool description"}
    success = await registry.update_tool(tool_id, updated_data)
    print(f"Tool update succeeded: {success}")
    
    # Retrieve a tool with its metadata
    tool = await registry.get_tool(tool_id)
    if tool and tool.tool_metadata_rel:
        print(f"Tool metadata usage count: {tool.tool_metadata_rel.usage_count}")

if __name__ == "__main__":
    asyncio.run(main()) 