# Dynamic Jira Software Cloud MCP Server

A premium, dynamic Model Context Protocol (MCP) server generated dynamically from Atlassian's `swagger.json` specification using the `FastMCP` framework in Python.

This server dynamically exposes **over 100 Jira Software Cloud REST API operations** as fully typed tools for Large Language Models (LLMs) to interact with, supporting Sstdio and Server-Sent Events (SSE) transports.

---

## 🏗 Architecture & Project Structure

The project has been architected following highly modular and decoupled software engineering best practices:

```
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

Create a local `.env` file in the root directory to customize the MCP server behavior and connect to your Jira instance:

```env
# Atlassian Jira Instance URL (e.g., https://your-domain.atlassian.net)
JIRA_BASE_URL=https://your-domain.atlassian.net

# Atlassian Account Email
JIRA_USERNAME=your-email@example.com

# Atlassian Account API Token
JIRA_API_TOKEN=your-jira-api-token

# Allowed HTTP Methods (comma-separated, e.g. "get" for read-only or "get,post,put,delete" for full CRUD)
ALLOWED_METHODS=get,post,put,delete

# MCP Server Settings
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

---

## 🚀 Running the Server

### 1. Locally with `uv` (Fastest)

Ensure you have [uv](https://github.com/astral-sh/uv) installed:

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

### 3. Automatically with Docker Compose (Recommended)

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

Run the asynchronous test client to verify connection to the running SSE server and list registered tools:

```bash
uv run python dynamic_jira_mcp_client.py
```

---

## 🛠 Features Included:
- **Reference Resolution (`$ref`)**: Recursively resolves and parses internal OpenAPI schemas.
- **Dynamic Parameter Mapping**: Handles Path parameters, Query parameters, and JSON Request bodies, registering them as native type annotations (e.g. `int`, `str`, `list`, `dict`) inside Python's function signatures.
- **SSE & Stdio Support**: Seamlessly toggles transport protocols.
- **Secure Non-Root Container**: Built with enterprise security best practices.
