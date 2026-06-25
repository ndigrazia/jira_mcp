# Use a lightweight official Python image
FROM python:3.12-slim

# Create a non-root system user and group
RUN groupadd -r mcp && useradd -r -g mcp -d /app mcp

# Set working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only requirements-related files first (owned by the non-root user)
COPY --chown=mcp:mcp pyproject.toml README.md /app/

# Install the dependencies listed in pyproject.toml
RUN pip install --no-cache-dir .

# Copy the rest of the application files (owned by the non-root user)
COPY --chown=mcp:mcp swagger.json /app/
COPY --chown=mcp:mcp dynamic_jira_mcp.py /app/
COPY --chown=mcp:mcp openapi/ /app/openapi/

# Expose port 8000 for SSE transport mode
EXPOSE 8000

# Set environment variables for the MCP server
ENV MCP_TRANSPORT=sse

# Switch to the non-root user
USER mcp

# Start the FastMCP server
CMD ["python", "dynamic_jira_mcp.py"]
