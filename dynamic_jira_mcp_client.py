import os
import asyncio
import logging
from dotenv import load_dotenv
from mcp import ClientSession

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-client")

async def test_client():
    transport = os.environ.get("MCP_CLIENT_TRANSPORT", "http").lower()
    host = os.environ.get("MCP_CLIENT_HOST", "localhost")
    port = os.environ.get("MCP_CLIENT_PORT", "8000")
    path = os.environ.get("MCP_CLIENT_PATH", "/mcp")

    # Enforce correct formatting for the path
    if path and not path.startswith("/"):
        path = f"/{path}"

    server_url = f"{host}:{port}{path}"

    client_id = os.environ.get("MCP_CLIENT_CLIENT_ID", "")
    client_secret = os.environ.get("MCP_CLIENT_CLIENT_SECRET", "")
    
    headers = {
        "client_id": client_id,
        "client_secret": client_secret
    }

    logger.info(f"Using MCP Client Transport: {transport.upper()}")
    logger.info(f"Connecting to MCP Server at {server_url}...")
    
    try:
        if transport == "http":
            import httpx
            from mcp.client.streamable_http import streamable_http_client
            http_client = httpx.AsyncClient(headers=headers)
            client_ctx = streamable_http_client(server_url, http_client=http_client)
        elif transport == "sse":
            from mcp.client.sse import sse_client
            client_ctx = sse_client(server_url, headers=headers)
        else:
            raise ValueError(f"Unsupported transport: {transport}. Must be 'http' or 'sse'.")

        # Establish connection to the running server
        async with client_ctx as streams:
            # sse_client returns 2 items, streamable_http_client returns 3 items
            read_stream, write_stream = streams[0], streams[1]
            
            # Create a client session over the read and write streams
            async with ClientSession(read_stream, write_stream) as session:
                logger.info("Initializing session with the MCP server...")
                await session.initialize()
                
                # List available tools on the server
                logger.info("Requesting available tools from server...")
                result = await session.list_tools()
                tools = result.tools
                
                logger.info(f"Successfully connected! Found {len(tools)} tools registered on the server.")
                
                # Print the first 10 tools as a sample
                print("\n" + "=" * 50)
                print(f"Jira MCP Server Tools List ({len(tools)} total):")
                print("=" * 50)
                for idx, tool in enumerate(tools[:10], start=1):
                    print(f"  {idx}. {tool.name}: {tool.description.splitlines()[0] if tool.description else 'No description'}")
                if len(tools) > 10:
                    print(f"  ... and {len(tools) - 10} more tools.")
                print("=" * 50 + "\n")
                
    except Exception as e:
        logger.exception("Failed to connect to the MCP server")

if __name__ == "__main__":
    asyncio.run(test_client())
