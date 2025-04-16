"""Tests for the Tool Registry core functionality."""

import pytest
import asyncio
from typing import Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from tool_registry.core.registry import ToolRegistry
from tool_registry.core.database import Database, Base
from tool_registry.models.tool import Tool as DBTool
from tool_registry.models.tool_metadata import ToolMetadata
from tool_registry.models.policy import Policy
from tool_registry.models.agent import Agent
from tool_registry.models.access_log import AccessLog
from tool_registry.models.credential import Credential
from tool_registry.schemas.tool import ToolCreate
from unittest.mock import MagicMock, patch

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
def mock_db_session():
    """Create a mock database session for testing."""
    session = MagicMock()
    query_mock = MagicMock()
    session.query.return_value = query_mock
    session.commit = MagicMock()
    session.close = MagicMock()
    return session, query_mock

@pytest.fixture
def test_tool():
    """Create a test tool for testing."""
    return {
        "name": "Test Tool",
        "description": "A tool for testing",
        "api_endpoint": "https://example.com/api",
        "auth_method": "API_KEY",
        "auth_config": {"header_name": "X-API-Key"},
        "params": {"text": {"type": "string", "required": True}},
        "version": "1.0.0",
        "tags": ["test", "utility"],
        "owner_id": uuid4()
    }

@pytest.fixture
def db_tool():
    """Create a DBTool instance for testing."""
    tool_id = uuid4()
    return DBTool(
        tool_id=tool_id,
        name="DB Test Tool",
        description="A tool from the database",
        api_endpoint="https://example.com/db-tool",
        auth_method="OAUTH",
        auth_config={"token_url": "https://example.com/token"},
        params={"query": {"type": "string", "required": True}},
        version="2.0.0",
        tags=["database", "utility"],
        owner_id=uuid4()
    )

@pytest.fixture
def tool_registry(mock_db_session):
    """Create a tool registry instance with mocked database."""
    session, _ = mock_db_session
    return ToolRegistry(session)

@pytest.mark.asyncio
async def test_register_tool_dict(tool_registry, mock_db_session, test_tool):
    """Test registering a tool using a dictionary."""
    session, query_mock = mock_db_session
    
    # Mock that the tool doesn't already exist
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    
    # Test register_tool method
    tool_id = await tool_registry.register_tool(test_tool)
    
    # Check the tool was added to the database
    assert session.add.called
    assert session.commit.called
    
    # Verify the ID was generated and returned
    assert isinstance(tool_id, UUID)
    
    # Verify the tool was added to the tools dict
    assert tool_id in tool_registry.tools
    assert tool_registry.tools[tool_id]["name"] == test_tool["name"]

@pytest.mark.asyncio
async def test_register_tool_object(tool_registry, mock_db_session, db_tool):
    """Test registering a tool using a DBTool object."""
    session, query_mock = mock_db_session
    
    # Mock that the tool doesn't already exist
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    
    # Test register_tool method
    tool_id = await tool_registry.register_tool(db_tool)
    
    # Check the tool was added to the database
    assert session.add.called
    assert session.commit.called
    
    # Verify the ID from the tool object was used
    assert tool_id == db_tool.tool_id
    
    # Verify the tool was added to the tools dict
    assert tool_id in tool_registry.tools
    assert tool_registry.tools[tool_id]["name"] == db_tool.name

@pytest.mark.asyncio
async def test_register_tool_existing(tool_registry, mock_db_session, test_tool):
    """Test registering a tool that already exists."""
    session, query_mock = mock_db_session
    
    # Mock that the tool already exists
    existing_tool = MagicMock()
    existing_tool.name = test_tool["name"]
    
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = existing_tool
    
    # Test register_tool method - should raise an error
    with pytest.raises(ValueError, match=f"Tool with name '{test_tool['name']}' already exists"):
        await tool_registry.register_tool(test_tool)
    
    # Check the tool was not added to the database
    assert not session.add.called
    assert not session.commit.called

@pytest.mark.asyncio
async def test_get_tool(tool_registry, mock_db_session, db_tool):
    """Test getting a tool by ID."""
    session, query_mock = mock_db_session
    
    # Mock that the tool exists
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = db_tool
    
    # Test get_tool method with UUID
    tool = await tool_registry.get_tool(db_tool.tool_id)
    
    # Verify the tool was returned
    assert tool == db_tool
    
    # Test with string ID
    tool = await tool_registry.get_tool(str(db_tool.tool_id))
    
    # Verify the tool was returned
    assert tool == db_tool

@pytest.mark.asyncio
async def test_get_tool_not_found(tool_registry, mock_db_session):
    """Test getting a tool that doesn't exist."""
    session, query_mock = mock_db_session
    
    # Mock that the tool doesn't exist
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    
    # Test get_tool method
    tool = await tool_registry.get_tool(uuid4())
    
    # Verify no tool was returned
    assert tool is None

@pytest.mark.asyncio
async def test_list_tools(tool_registry, mock_db_session):
    """Test listing all tools."""
    session, query_mock = mock_db_session
    
    # Mock the list of tools
    tools = [MagicMock(), MagicMock()]
    query_mock.all.return_value = tools
    
    # Test list_tools method
    result = await tool_registry.list_tools()
    
    # Verify the tools were returned
    assert result == tools

@pytest.mark.asyncio
async def test_search_tools(tool_registry, mock_db_session):
    """Test searching for tools."""
    session, query_mock = mock_db_session
    
    # Mock the initial query results (name/description matches)
    tool1 = MagicMock()
    tool1.tool_id = uuid4()
    tool1.name = "First Tool"
    
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.all.return_value = [tool1]
    
    # Mock the all() query for tag matching
    tool2 = MagicMock()
    tool2.tool_id = uuid4()
    tool2.name = "Second Tool"
    tool2.tags = ["test", "query"]
    
    query_mock.all.return_value = [tool1, tool2]
    
    # Test search_tools method
    result = await tool_registry.search_tools("test")
    
    # Verify both tools were returned
    assert len(result) == 2
    assert tool1 in result
    assert tool2 in result

@pytest.mark.asyncio
async def test_update_tool(tool_registry, mock_db_session, db_tool):
    """Test updating a tool."""
    session, query_mock = mock_db_session
    
    # Mock that the tool exists
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = db_tool
    
    # Create update data
    update_data = {
        "name": "Updated Tool",
        "description": "Updated description",
        "version": "2.1.0"
    }
    
    # Test update_tool method
    result = await tool_registry.update_tool(db_tool.tool_id, update_data)
    
    # Verify the result
    assert result is True
    
    # Verify the tool was updated
    assert db_tool.name == "Updated Tool"
    assert db_tool.description == "Updated description"
    assert db_tool.version == "2.1.0"
    
    # Check the database was updated
    assert session.commit.called

@pytest.mark.asyncio
async def test_update_tool_not_found(tool_registry, mock_db_session):
    """Test updating a tool that doesn't exist."""
    session, query_mock = mock_db_session
    
    # Mock that the tool doesn't exist
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    
    # Create update data
    update_data = {
        "name": "Updated Tool",
        "description": "Updated description"
    }
    
    # Test update_tool method - should raise an error
    tool_id = uuid4()
    with pytest.raises(ValueError, match=f"Tool with ID {tool_id} not found"):
        await tool_registry.update_tool(tool_id, update_data)
    
    # Check the database was not updated
    assert not session.commit.called

@pytest.mark.asyncio
async def test_delete_tool(tool_registry, mock_db_session, db_tool):
    """Test deleting a tool."""
    session, query_mock = mock_db_session
    
    # Mock that the tool exists
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = db_tool
    
    # Add tool to in-memory store
    tool_registry.tools[db_tool.tool_id] = {"name": db_tool.name}
    
    # Test delete_tool method
    result = await tool_registry.delete_tool(db_tool.tool_id)
    
    # Verify the result
    assert result is True
    
    # Verify the tool was deleted from database
    assert session.delete.called
    assert session.commit.called
    
    # Verify the tool was removed from in-memory store
    assert db_tool.tool_id not in tool_registry.tools

@pytest.mark.asyncio
async def test_delete_tool_not_found(tool_registry, mock_db_session):
    """Test deleting a tool that doesn't exist."""
    session, query_mock = mock_db_session
    
    # Mock that the tool doesn't exist
    filter_mock = MagicMock()
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    
    # Test delete_tool method
    result = await tool_registry.delete_tool(uuid4())
    
    # Verify the result
    assert result is False
    
    # Verify no deletion was attempted
    assert not session.delete.called
    assert not session.commit.called 