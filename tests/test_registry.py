"""Tests for the Tool Registry core functionality."""

import pytest
from uuid import UUID, uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from tool_registry.core.registry import ToolRegistry
from tool_registry.core.database import Database, Base
from tool_registry.models.tool import Tool
from tool_registry.models.tool_metadata import ToolMetadata
from tool_registry.models.policy import Policy
from tool_registry.models.agent import Agent
from tool_registry.models.access_log import AccessLog
from tool_registry.models.credential import Credential
from tool_registry.schemas.tool import ToolCreate

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a test database and yield a Session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_tool():
    """Create a test tool instance."""
    return Tool(
        tool_id=uuid4(),
        name="Test Tool",
        description="A test tool",
        api_endpoint="http://test.com/api",
        auth_method="API_KEY",
        auth_config={},
        params={},
        version="1.0.0",
        tags=["test"],
        owner_id=uuid4()
    )

@pytest.fixture
def test_metadata():
    """Create a test tool metadata instance."""
    return ToolMetadata(
        schema_data={"inputs": {}, "outputs": {}},
        schema_version="1.0",
        schema_type="openapi",
        inputs={},
        outputs={},
        documentation_url="http://test.com/docs",
        tool_id=uuid4()
    )

@pytest.fixture
def tool_registry(db_session):
    """Create a test tool registry instance."""
    return ToolRegistry(db_session)

@pytest.mark.asyncio
async def test_register_tool(tool_registry, test_tool):
    """Test registering a tool."""
    tool_id = await tool_registry.register_tool(test_tool)
    assert isinstance(tool_id, UUID)
    
    # Verify the tool can be retrieved
    retrieved_tool = await tool_registry.get_tool(tool_id)
    assert retrieved_tool is not None
    assert retrieved_tool.tool_id == tool_id
    assert retrieved_tool.name == test_tool.name
    assert retrieved_tool.description == test_tool.description
    assert retrieved_tool.version == test_tool.version

@pytest.mark.asyncio
async def test_duplicate_tool_name(tool_registry, test_tool):
    """Test registering a tool with a duplicate name."""
    await tool_registry.register_tool(test_tool)
    
    # Try to register another tool with the same name
    duplicate_tool = Tool(
        tool_id=uuid4(),
        name=test_tool.name,
        description="Another tool",
        version="2.0.0",
        api_endpoint="https://api.example.com/another",
        auth_method="API_KEY",
        auth_config={},
        params={}
    )
    
    with pytest.raises(ValueError):
        await tool_registry.register_tool(duplicate_tool)

@pytest.mark.asyncio
async def test_get_nonexistent_tool(tool_registry):
    """Test getting a tool that doesn't exist."""
    tool = await tool_registry.get_tool(UUID('00000000-0000-0000-0000-000000000000'))
    assert tool is None

@pytest.mark.asyncio
async def test_list_tools(tool_registry, test_tool):
    """Test listing all tools."""
    await tool_registry.register_tool(test_tool)
    tools = await tool_registry.list_tools()
    assert len(tools) == 1
    assert tools[0].tool_id == test_tool.tool_id
    assert tools[0].name == test_tool.name

@pytest.mark.asyncio
async def test_search_tools(tool_registry, test_tool):
    """Test searching for tools."""
    await tool_registry.register_tool(test_tool)
    
    # Search by name
    tools = await tool_registry.search_tools("Test Tool")
    assert len(tools) == 1
    assert tools[0].tool_id == test_tool.tool_id
    
    # Search by description
    tools = await tool_registry.search_tools("test tool")
    assert len(tools) == 1
    assert tools[0].tool_id == test_tool.tool_id
    
    # Search with no results
    tools = await tool_registry.search_tools("nonexistent")
    assert len(tools) == 0

@pytest.mark.asyncio
async def test_update_tool(tool_registry, test_tool):
    """Test updating a tool."""
    tool_id = await tool_registry.register_tool(test_tool)
    
    # Update the tool
    updated_tool = Tool(
        tool_id=tool_id,
        name="updated_tool",
        description="Updated description",
        version="2.0.0",
        api_endpoint="https://api.example.com/updated",
        auth_method="NONE",
        auth_config={},
        params={}
    )
    
    success = await tool_registry.update_tool(tool_id, updated_tool)
    assert success
    
    # Verify the update
    retrieved_tool = await tool_registry.get_tool(tool_id)
    assert retrieved_tool.name == "updated_tool"
    assert retrieved_tool.description == "Updated description"
    assert retrieved_tool.version == "2.0.0"
    assert retrieved_tool.auth_method == "NONE"

@pytest.mark.asyncio
async def test_delete_tool(tool_registry, test_tool):
    """Test deleting a tool."""
    tool_id = await tool_registry.register_tool(test_tool)
    
    # Delete the tool
    success = await tool_registry.delete_tool(tool_id)
    assert success
    
    # Verify the tool is gone
    retrieved_tool = await tool_registry.get_tool(tool_id)
    assert retrieved_tool is None 