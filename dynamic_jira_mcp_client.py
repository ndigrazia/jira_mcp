import asyncio
import logging
from mcp import ClientSession
from mcp.client.sse import sse_client

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-client")

async def test_client():
    server_url = "http://127.0.0.1:8000/sse"
    logger.info(f"Connecting to MCP SSE Server at {server_url}...")
    
    try:
        # Establish connection to the running SSE server
        async with sse_client(server_url) as (read_stream, write_stream):
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
