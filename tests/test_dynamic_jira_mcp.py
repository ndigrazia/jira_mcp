import os
import sys
import pytest
import inspect
import logging
from typing import Any

# Configure logging to print messages to the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-jira-mcp")

# Ensure current directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dynamic_jira_mcp import mcp, api_client

def test_swagger_loading():
    """Test that swagger.json is loaded correctly through OpenAPIClient."""
    logger.info("Running test_swagger_loading...")
    assert isinstance(api_client.swagger_data, dict)
    assert "paths" in api_client.swagger_data
    assert "components" in api_client.swagger_data
    logger.info("Successfully verified swagger.json loading.")

def test_resolve_ref():
    """Test reference resolution using OpenAPIClient."""
    logger.info("Running test_resolve_ref...")
    ref_str = "#/components/schemas/AvatarUrlsBean"
    resolved = api_client.resolve_ref(ref_str)
    assert isinstance(resolved, dict)
    assert "properties" in resolved
    assert "16x16" in resolved["properties"]
    logger.info("Successfully verified component reference resolution.")

def test_sanitize_name():
    """Test operation and parameter name sanitization on OpenAPIClient."""
    logger.info("Running test_sanitize_name...")
    assert api_client.sanitize_name("get-all-boards") == "get_all_boards"
    assert api_client.sanitize_name("getAllBoards") == "getAllBoards"
    assert api_client.sanitize_name("123board") == "_123board"
    logger.info("Successfully verified identifier name sanitization.")

def test_get_python_type():
    """Test OpenAPI type mapping to Python types via OpenAPIClient."""
    logger.info("Running test_get_python_type...")
    assert api_client.get_python_type({"type": "string"}) == str
    assert api_client.get_python_type({"type": "integer"}) == int
    assert api_client.get_python_type({"type": "boolean"}) == bool
    assert api_client.get_python_type({"type": "array"}) == list
    assert api_client.get_python_type({"type": "object"}) == dict
    logger.info("Successfully verified type mapping logic.")

@pytest.mark.anyio
async def test_registered_tools_count():
    """Test that all 105 Jira API tools are registered correctly with FastMCP."""
    logger.info("Running test_registered_tools_count...")
    tools = await mcp._local_provider.list_tools()
    assert len(tools) == 105
    logger.info(f"Successfully verified that {len(tools)} tools are registered with FastMCP.")

@pytest.mark.anyio
async def test_specific_tool_signature():
    """Test that a specific tool has the expected signature and schema."""
    logger.info("Running test_specific_tool_signature...")
    tools = await mcp._local_provider.list_tools()
    get_all_boards_tool = next((t for t in tools if t.name == "getAllBoards"), None)
    
    assert get_all_boards_tool is not None
    assert "Get all boards" in get_all_boards_tool.description
    
    # Verify signature parameters
    sig = inspect.signature(get_all_boards_tool.fn)
    assert "startAt" in sig.parameters
    assert "maxResults" in sig.parameters
    
    # Query parameters should be optional and default to None or specified default
    assert sig.parameters["startAt"].default == 0
    assert sig.parameters["maxResults"].default == 50
    logger.info("Successfully verified dynamic function signature generation.")
