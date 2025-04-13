import pytest
from uuid import UUID
from sqlalchemy import create_engine
from tool_registry.core.registry import Tool, ToolMetadata, ToolRegistry
from tool_registry.core.database import Database, Base
import uuid
import asyncio

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)

@pytest.fixture(scope="function")
def db():
    """Create a test database and yield a Database instance."""
    Base.metadata.create_all(bind=engine)
    db = Database(TEST_DATABASE_URL)
    db.init_db()  # Initialize the database by creating all tables
    yield db
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def tool_metadata():
    """Create a sample tool metadata."""
    return ToolMetadata(
        schema_version="1.0",
        inputs={"text": {"type": "string"}},
        outputs={"result": {"type": "string"}}
    )

@pytest.fixture
def tool(tool_metadata):
    """Create a sample tool."""
    return Tool(
        tool_id=uuid.uuid4(),
        name="test_tool",
        description="A test tool",
        version="1.0.0",
        tool_metadata_rel=tool_metadata,
        endpoint="https://api.example.com/test",
        auth_required=True,
        auth_type="api_key",
        rate_limit=100,
        cost_per_call=0.01
    )

@pytest.mark.asyncio
async def test_register_tool(db, tool):
    """Test registering a tool."""
    registry = ToolRegistry(db)
    tool_id = await registry.register_tool(tool)
    assert isinstance(tool_id, UUID)
    
    # Verify the tool can be retrieved
    retrieved_tool = await registry.get_tool(tool_id)
    assert retrieved_tool is not None
    assert retrieved_tool.tool_id == tool_id
    assert retrieved_tool.name == tool.name
    assert retrieved_tool.description == tool.description
    assert retrieved_tool.version == tool.version
    assert retrieved_tool.tool_metadata_rel.schema_version == tool.tool_metadata_rel.schema_version

@pytest.mark.asyncio
async def test_duplicate_tool_name(db, tool):
    """Test registering a tool with a duplicate name."""
    registry = ToolRegistry(db)
    await registry.register_tool(tool)
    
    # Try to register another tool with the same name
    duplicate_tool = Tool(
        tool_id=uuid.uuid4(),
        name=tool.name,
        description="Another tool",
        version="2.0.0",
        tool_metadata_rel=ToolMetadata(
            schema_version="1.0",
            inputs={"query": {"type": "string"}},
            outputs={"result": {"type": "string"}}
        ),
        endpoint="https://api.example.com/another",
        auth_required=True
    )
    
    with pytest.raises(ValueError):
        await registry.register_tool(duplicate_tool)

@pytest.mark.asyncio
async def test_get_nonexistent_tool(db):
    """Test getting a tool that doesn't exist."""
    registry = ToolRegistry(db)
    tool = await registry.get_tool(UUID('00000000-0000-0000-0000-000000000000'))
    assert tool is None

@pytest.mark.asyncio
async def test_list_tools(db, tool):
    """Test listing all tools."""
    registry = ToolRegistry(db)
    await registry.register_tool(tool)
    tools = await registry.list_tools()
    assert len(tools) == 1
    assert tools[0].tool_id == tool.tool_id
    assert tools[0].name == tool.name

@pytest.mark.asyncio
async def test_search_tools(db, tool):
    """Test searching for tools."""
    registry = ToolRegistry(db)
    await registry.register_tool(tool)
    
    # Search by name
    tools = await registry.search_tools("test_tool")
    assert len(tools) == 1
    assert tools[0].tool_id == tool.tool_id
    
    # Search by description
    tools = await registry.search_tools("test tool")
    assert len(tools) == 1
    assert tools[0].tool_id == tool.tool_id
    
    # Search with no results
    tools = await registry.search_tools("nonexistent")
    assert len(tools) == 0

@pytest.mark.asyncio
async def test_update_tool(db, tool):
    """Test updating a tool."""
    registry = ToolRegistry(db)
    tool_id = await registry.register_tool(tool)
    
    # Update the tool
    updated_tool = Tool(
        tool_id=tool_id,
        name="updated_tool",
        description="Updated description",
        version="2.0.0",
        tool_metadata_rel=ToolMetadata(
            schema_version="1.1",
            inputs={"query": {"type": "string"}},
            outputs={"result": {"type": "object"}}
        ),
        endpoint="https://api.example.com/updated",
        auth_required=False
    )
    
    success = await registry.update_tool(tool_id, updated_tool)
    assert success
    
    # Verify the update
    retrieved_tool = await registry.get_tool(tool_id)
    assert retrieved_tool.name == "updated_tool"
    assert retrieved_tool.description == "Updated description"
    assert retrieved_tool.version == "2.0.0"
    assert not retrieved_tool.auth_required

@pytest.mark.asyncio
async def test_delete_tool(db, tool):
    """Test deleting a tool."""
    registry = ToolRegistry(db)
    tool_id = await registry.register_tool(tool)
    
    # Delete the tool
    success = await registry.delete_tool(tool_id)
    assert success
    
    # Verify the tool is gone
    retrieved_tool = await registry.get_tool(tool_id)
    assert retrieved_tool is None 