# Adding Agents

How to build a new agent for this platform.

## Quick start

```bash
# 1. Scaffold
uv run python -m agent_core.scaffold my-agent --description "What this agent does"

# 2. Edit your tools and config
#    agents/my-agent/src/my_agent/tools.py
#    agents/my-agent/src/my_agent/config.py

# 3. Install
uv sync

# 4. Validate
uv run python -m agent_core.validate

# 5. Run — the router auto-discovers your agent
uv run --package router-agent python -m router.main
```

## The plugin contract

Every agent must be a Python package in `agents/` that exports two things from `__init__.py`:

```python
# agents/my-agent/src/my_agent/__init__.py
"""My agent."""

from . import tools
from .config import config

__all__ = ["config", "tools"]
```

- **`config`** — an `AgentConfig` instance (from `agent_core`)
- **`tools`** — the module containing your `@tool` functions

The router auto-discovers all packages in `agents/` (except `router` itself).

## Writing tools

Tools are regular Python functions with the `@tool` decorator. The AI model reads the function's docstring and type annotations to decide when and how to call it.

```python
from agent_framework import tool
from typing import Annotated
from pydantic import Field

@tool
def lookup_status(
    ticket_id: Annotated[str, Field(description="Ticket ID, e.g. INC-1234")],
) -> str:
    """Look up the current status of a support ticket."""
    # Your logic here — call an API, query a database, etc.
    return f"Ticket {ticket_id} is currently in progress."
```

### Rules for tools

- The **docstring** is what the AI model sees. Make it clear and specific.
- Use **type annotations** with `Annotated` + `Field(description=...)` for parameters.
- Return a **string** — the model reads your return value.
- Keep tools **focused** — one tool, one job.
- Tools that modify data should use `@tool(approval_mode="always_require")`:

```python
@tool(approval_mode="always_require")
def delete_account(user_id: str) -> str:
    """Delete a user account. Requires human approval."""
    ...
```

## Writing config

The `AgentConfig` defines your agent's identity, behavior, and capabilities.

```python
from agent_core import AgentConfig

config = AgentConfig(
    name="my-agent",
    description="One-line summary",
    instructions="""You are...

Rules:
- Use your tools to look up information.
- Be concise and factual.
- If you don't know, say so.
""",
    tools=["lookup_status", "create_ticket"],
    file_search_enabled=False,
    model="gpt-4.1",
)
```

### Config fields

| Field | Default | What it does |
|-------|---------|-------------|
| `name` | (required) | Unique agent name |
| `instructions` | (required) | System prompt — defines agent behavior |
| `description` | `""` | Triage reads this to decide which agent handles a question |
| `tools` | `[]` | List of tool function names (or `mcp:<name>:<url>`) |
| `file_search_enabled` | `False` | Enable RAG via Azure vector store |
| `model` | `"gpt-4.1"` | Azure OpenAI deployment name |
| `max_output_tokens` | `2048` | Max response length |
| `max_conversation_turns` | `50` | Max messages before session limit |
| `max_input_length` | `4000` | Max chars per user message |

### YAML config (alternative)

```yaml
# agents/my-agent/agent.yaml
name: my-agent
description: One-line summary
model: gpt-4.1
instructions: |
  You are...
tools:
  - lookup_status
  - create_ticket
file_search_enabled: false
```

Load with: `config = AgentConfig.from_yaml("agent.yaml")`

## Adding RAG (knowledge base)

1. Drop documents in `agents/my-agent/knowledge/` (PDF, MD, DOCX, HTML, CSV, JSON)
2. Upload to Azure vector store:

```bash
cd agents/my-agent
uv run python -m agent_core.knowledge upload
```

3. Copy the `VECTOR_STORE_ID` to your `.env`
4. Set `file_search_enabled=True` in your config

The agent can now search your documents to answer questions.

## Connecting MCP tools

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) lets you connect external tools without writing code.

```python
config = AgentConfig(
    tools=[
        "local_function",
        "mcp:confluence:http://localhost:3000/mcp",
        "mcp:jira:http://localhost:3001/mcp",
    ],
)
```

The platform resolves `mcp:` prefixed tools automatically via `client.get_mcp_tool()`.

## Testing your agent

### Unit tests (no Azure needed)

```python
# agents/my-agent/tests/test_tools.py
from my_agent.tools import lookup_status

def test_lookup_known():
    result = lookup_status("INC-1234")
    assert "INC-1234" in result
```

Run: `uv run pytest agents/my-agent/tests/`

### Evaluation tests (requires Azure)

```python
# evals/test_my_agent.py
import pytest

pytestmark = pytest.mark.eval

async def test_routes_to_my_agent(workflow):
    events = [e async for e in workflow.run_stream("my question")]
    # Assert the right agent handled it
```

Run: `uv run pytest evals/ -m eval`

## Validating all agents

```bash
uv run python -m agent_core.validate
```

Checks: config/tools exports, tool callability, no duplicate names.

## Agent directory structure

```
agents/my-agent/
├── pyproject.toml              # Package config (depends on agent-core)
├── src/my_agent/
│   ├── __init__.py             # Exports: config, tools
│   ├── config.py               # AgentConfig instance
│   └── tools.py                # @tool functions
├── knowledge/                  # Documents for RAG (optional)
└── tests/
    └── __init__.py
```

## Checklist

- [ ] `config.name` is unique
- [ ] `config.description` clearly says what the agent handles
- [ ] `config.instructions` defines scope and rules
- [ ] All tools have docstrings and type annotations
- [ ] Tools return strings
- [ ] Write-operations use `approval_mode="always_require"`
- [ ] `uv run python -m agent_core.validate` passes
- [ ] Unit tests exist for your tools
