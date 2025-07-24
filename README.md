# MCP Server Example

## Usage
```
# Default
uv run sse-server

# Using custom port
uv run sse-server --port 8000

# Custom logging level
uv run sse-server --log-level DEBUG

# Enable JSON responses instead of SSE streams
uv run sse-server --json-response
```

### Reference
[python-sdk/examples/servers
/simple-streamablehttp-stateless](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/servers/simple-streamablehttp-stateless)