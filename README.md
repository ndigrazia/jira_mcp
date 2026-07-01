# 🛠️ Dynamic Jira Software Cloud MCP Server

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![MCP Specification](https://img.shields.io/badge/mcp-1.0.0-orange.svg)](https://modelcontextprotocol.io)
[![FastMCP](https://img.shields.io/badge/framework-FastMCP-green.svg)](https://github.com/jestor/fastmcp)

An enterprise-ready, premium **Model Context Protocol (MCP)** server generated dynamically from Atlassian's official Jira Cloud REST API specifications (`swagger.json`). Built on top of the robust **FastMCP** framework, it exposes **over 100 Jira Software Cloud operations** as fully typed tools for LLMs (such as Claude).

This server supports both **Stdio** (local) and **SSE** (Server-Sent Events) transport modes, enabling seamless integration into any LLM environment, from desktop applications to cloud-native microservices.

---

## 🚀 Key Capabilities

- **Automated Tool Registration**: Parses Atlassian's OpenAPI 3.0 specs to register and expose 100+ fully documented tools.
- **Dynamic Parameter Resolution**: Resolves `$ref` types recursively and maps path, query, and request body variables into native Python signatures (`str`, `int`, `bool`, `list`, `dict`) with default values.
- **Granular Access Control**: Limit operations using `ALLOWED_METHODS` (e.g. read-only `get` or full `get,post,put,delete` CRUD permissions).
- **Flexible Transports**: Run locally with standard high-performance Stdio or expose via a production-grade SSE server.
- **Secure Containerization**: Built using security best practices with a hardened, non-root user inside a secure Docker base.

---

## 📁 Repository Blueprint

```text
├── .env                         # Environment configurations
├── Dockerfile                   # hardened, multi-stage production Docker image
├── docker-compose.yml           # Container orchestration template for SSE server
├── pyproject.toml               # Poetry/uv dependency specs and pytest configurations
├── dynamic_jira_mcp.py          # FastMCP server launcher & tool generation engine
├── dynamic_jira_mcp_client.py   # Asynchronous test client with custom client header validation
├── swagger.json                 # Official Atlassian Jira Software Cloud OpenAPI schema
├── openapi/                     # Decoupled core modules
│   ├── __init__.py
│   └── openapi_client.py        # Schema parser, type mapper, and async HTTP engine
└── tests/                       # Complete automated unit & integration testing suite
    └── test_dynamic_jira_mcp.py # Validation suite testing client resolution, mapping & registers
```

---

## ⚙️ Setup and Configuration

Create a local `.env` file in the root directory:

```env
# Atlassian Jira Instance URL
JIRA_BASE_URL=https://your-domain.atlassian.net

# Jira Username (Account Email)
JIRA_USERNAME=your-email@example.com

# Jira API Token (Not your login password!)
JIRA_API_TOKEN=your-jira-api-token

# API Operations Scope Control (comma-separated HTTP methods)
ALLOWED_METHODS=get,post,put,delete

# Server Transport Configuration
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Client Configuration
MCP_CLIENT_TRANSPORT=http
MCP_CLIENT_HOST=http://localhost
MCP_CLIENT_PORT=8000
MCP_CLIENT_PATH=/mcp

# Optional Client Security Headers
MCP_CLIENT_CLIENT_ID=your-client-id
MCP_CLIENT_CLIENT_SECRET=your-client-secret
```

---

## 🖥 Claude Desktop Integration

Integrate the MCP server with Claude Desktop by adding it to your `claude_desktop_config.json` configuration file:

### Local Stdio Integration (Recommended)

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

## 🏃 Launching the Server

### 1. Locally with `uv`

Ensure you have [uv](https://github.com/astral-sh/uv) installed, then run:

```bash
uv run python dynamic_jira_mcp.py
```

### 2. Using Docker

```bash
# Build the secure image
docker build -t jira-mcp-server .

# Run the container with environment variables
docker run -p 8000:8000 --env-file .env jira-mcp-server
```

### 3. Using Docker Compose

```bash
# Spin up in detached mode
docker compose up -d

# View log stream
docker logs -f jira-mcp-server
```

---

## 🧪 Testing & Diagnostics

### 1. Execute Automated Pytest Suite

Run our comprehensive verification suite:

```bash
uv run python -m pytest -o log_cli=true --log-cli-level=INFO tests/
```

### 2. Run Asynchronous Test Client

To verify your SSE/HTTP server connectivity along with proper headers transmission:

```bash
uv run python dynamic_jira_mcp_client.py
```

---

## 🤝 Troubleshooting & Common Issues

- **401 Unauthorized**: Ensure your `JIRA_USERNAME` is correct and `JIRA_API_TOKEN` is generated properly from your Atlassian Security Panel.
- **403 Forbidden**: Confirm that the requested action is permitted for your user account inside your target Jira project space and matches allowed settings inside `ALLOWED_METHODS`.
- **SSE Connection Timeout**: Ensure `MCP_HOST` is bound to `0.0.0.0` inside containerized setups, allowing public port-mapping to resolve correctly on the host network.
