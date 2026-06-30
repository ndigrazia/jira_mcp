# Dynamic Jira Software Cloud MCP Server

A premium, dynamic Model Context Protocol (MCP) server generated dynamically from Atlassian's official `swagger.json` specification using the `FastMCP` framework in Python.

This server dynamically exposes **over 100 Jira Software Cloud REST API operations** as fully typed tools for Large Language Models (LLMs) to interact with, supporting both **Stdio** and **Server-Sent Events (SSE)** transports.

---

## ✨ Features

- **Dynamic API Generation**: Automatically parses Jira's Swagger/OpenAPI spec to register and expose 105 tools.
- **Reference Resolution (`$ref`)**: Recursively resolves and parses internal OpenAPI schema definitions.
- **Dynamic Parameter Mapping**: Extracts Path parameters, Query parameters, and JSON Request bodies, mapping them to native Python type annotations (e.g., `int`, `str`, `list`, `dict`) inside dynamic function signatures for LLM introspection.
- **Method Scoping / Security**: Easily restrict LLMs to specific HTTP methods (e.g., read-only with `ALLOWED_METHODS=get`, or write access with `ALLOWED_METHODS=get,post,put,delete`).
- **SSE & Stdio Support**: Seamlessly switch between Stdio (ideal for local IDEs and Claude Desktop) and SSE (ideal for cloud-native web client connections).
- **Enterprise Docker Image**: Formulated with security best practices, using a secure, non-root system user.

---

## 🏗 Architecture & Project Structure

The project is structured following highly modular and decoupled software engineering best practices:

```text
├── .env                         # Local environment configuration
├── Dockerfile                   # Safe, non-root system user Docker image setup
├── docker-compose.yml           # Automated multi-container configuration
├── pyproject.toml               # Python project configuration and dependency list
├── dynamic_jira_mcp.py          # FastMCP server registration and transport hub
├── dynamic_jira_mcp_client.py   # Async MCP Client for testing the running SSE server
├── swagger.json                 # Atlassian Jira Software Cloud API OpenAPI 3.0 specification
├── openapi/                     # Decoupled OpenAPI extraction and client package
│   ├── __init__.py
│   └── openapi_client.py        # Generic OpenAPI spec parser and async HTTP request execution
└── tests/                       # Fully automated test suite
    └── test_dynamic_jira_mcp.py # Pytest-compatible tests with live console logging
```

---

## ⚙️ Configuration & Environment Variables

Create a local `.env` file in the root directory to customize the MCP server and client behavior:

```env
# Atlassian Jira Instance URL (e.g., https://your-domain.atlassian.net)
JIRA_BASE_URL=https://your-domain.atlassian.net

# Atlassian Account Email
JIRA_USERNAME=your-email@example.com

# Atlassian Account API Token
JIRA_API_TOKEN=your-jira-api-token

# Allowed HTTP Methods (comma-separated: e.g., "get" for read-only or "get,post,put,delete" for full CRUD)
ALLOWED_METHODS=get,post,put,delete

# MCP Server Settings
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8000

# MCP Client Settings (for dynamic_jira_mcp_client.py)
MCP_CLIENT_TRANSPORT=sse
MCP_CLIENT_HOST=localhost
MCP_CLIENT_PORT=8000
MCP_CLIENT_PATH=/mcp
```

---

## 🖥 Claude Desktop Integration

To use this dynamic Jira server inside Claude Desktop, add it to your configuration file (typically located at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows).

### Configuration for Stdio Mode (Recommended for local setup)

Ensure your `ALLOWED_METHODS` and authentication keys are set properly:

```json
{
  "mcpServers": {
    "jira-mcp-stdio": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/home/ollama/python/jira/mcp",
        "python",
        "/home/ollama/python/jira/mcp/dynamic_jira_mcp.py"
      ],
      "env": {
        "JIRA_BASE_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your-email@example.com",
        "JIRA_API_TOKEN": "your-jira-api-token",
        "ALLOWED_METHODS": "get,post,put,delete",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

---

## 🚀 Running the Server

### 1. Locally with `uv` (Fastest)

Make sure you have [uv](https://github.com/astral-sh/uv) installed, then run:

```bash
# Install dependencies and launch the server
uv run python dynamic_jira_mcp.py
```

### 2. Containerized with Docker

This container is strictly configured with a **non-root system user** for industry-standard production safety.

```bash
# Build the Docker image
docker build -t jira-mcp-server .

# Run the container mapping port 8000
docker run -p 8000:8000 --env-file .env jira-mcp-server
```

### 3. Automatically with Docker Compose (Recommended for SSE)

To spin up, build (if missing), and tag the image, launch via compose:

```bash
# Launch the containerized server in detached mode
docker compose up -d

# View live server logs
docker logs -f jira-mcp-server
```

---

## 🧪 Testing and Introspection

### 1. Real-time Console Log Tests via Pytest

Run the comprehensive async testing suite with full live logging outputs:

```bash
uv run python -m pytest -o log_cli=true --log-cli-level=INFO tests/
```

### 2. Connect via the MCP Client Component

If you run the server using `MCP_TRANSPORT=sse` (port `8000`), you can test connection, list registered tools, and introspect signatures by running the asynchronous test client:

```bash
uv run python dynamic_jira_mcp_client.py
```
