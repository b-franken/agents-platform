# MCP Server Example

Exposes the helpdesk knowledge base as a [Model Context Protocol](https://modelcontextprotocol.io/) server. Any MCP-compatible client can connect and search the KB.

## Run

```bash
uv run python examples/mcp-server/main.py
```

The server starts on `http://localhost:8100/mcp`.

## Connect from an agent

Add the MCP tool to any agent's `config.yaml`:

```yaml
tools:
  - "mcp:helpdesk-kb:http://localhost:8100/mcp"
```

The platform's factory resolves `mcp:` prefixed tools via `client.get_mcp_tool()`.

## Tools exposed

| Tool | Description |
|------|-------------|
| `search_knowledge_base` | Search KB articles by keyword |
| `list_articles` | List all available articles |
