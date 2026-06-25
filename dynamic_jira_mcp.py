import os
import inspect
import logging
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from openapi.openapi_client import OpenAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-mcp")

# Initialize FastMCP Server
mcp = FastMCP("Jira", instructions="MCP Server for Jira Software Cloud REST API, generated from Swagger definition.")

# Load OpenAPI/Swagger JSON path
SWAGGER_PATH = os.path.join(os.path.dirname(__file__), "swagger.json")

# Instantiate decoupled OpenAPI Client
api_client = OpenAPIClient(SWAGGER_PATH)

def build_dynamic_tool(method: str, path_template: str, op_data: Dict[str, Any]):
    """Register an OpenAPI operation as a FastMCP tool using the decoupled OpenAPIClient."""
    (
        tool_name,
        summary,
        description,
        path_params_info,
        query_params_info,
        body_params_info,
        raw_params,
    ) = api_client.extract_operation_metadata(method, path_template, op_data)

    # Construct clean docstrings for LLMs
    docstring_parts = [f"{summary}\n\n{description}\n" if description else f"{summary}\n"]
    for p_name, _, _, p_desc in raw_params:
        docstring_parts.append(f":param {p_desc}")

    # Tool handler closure invoking OpenAPI Client request execution
    async def tool_handler(*args, **kwargs):
        return await api_client.execute_request(
            method,
            path_template,
            path_params_info,
            query_params_info,
            body_params_info,
            kwargs
        )

    # Setup function properties dynamically for FastMCP signature introspection
    tool_handler.__name__ = tool_name
    tool_handler.__doc__ = "\n".join(docstring_parts)
    
    annotations = {}
    inspect_params = []
    
    # Map parameters to signature parameters list
    for p_name, p_type, p_default, _ in raw_params:
        annotations[p_name] = p_type
        inspect_params.append(
            inspect.Parameter(
                name=p_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=p_type,
                default=p_default
            )
        )
        
    annotations["return"] = Any
    tool_handler.__annotations__ = annotations
    tool_handler.__signature__ = inspect.Signature(inspect_params, return_annotation=Any)
    
    # Register tool function with FastMCP
    mcp.tool()(tool_handler)
    logger.debug(f"Registered tool: {tool_name} for {method.upper()} {path_template}")

# Parse allowed HTTP methods from environment variable (default: get,post,put,delete)
ALLOWED_METHODS_ENV = os.environ.get("ALLOWED_METHODS", "get,post,put,delete")
allowed_methods = {m.strip().lower() for m in ALLOWED_METHODS_ENV.split(",") if m.strip()}
logger.info(f"Registering tools for allowed HTTP methods: {allowed_methods}")

# Register all paths from loaded Swagger spec
registered_count = 0
for path, methods in api_client.swagger_data.get("paths", {}).items():
    for method, op_data in methods.items():
        if method.lower() in allowed_methods:
            try:
                build_dynamic_tool(method, path, op_data)
                registered_count += 1
            except Exception as e:
                logger.error(f"Error building tool for {method.upper()} {path}: {e}")

logger.info(f"Successfully generated and registered {registered_count} Jira API tools from swagger.json.")

# Run fastmcp as SSE server
if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "sse")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    logger.info(f"Starting FastMCP server with transport: {transport} on {host}:{port}")
    mcp.run(transport=transport, host=host, port=port)
