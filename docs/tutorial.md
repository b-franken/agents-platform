# Tutorial: Build Your First Agent

This guide walks you through building a new agent from scratch. By the end, you'll understand the plugin contract, tool definition, and how auto-discovery works.

**Time**: ~15 minutes
**Requires**: A working setup ([Getting Started](getting-started.md))

## What we're building

A greeting agent that responds with personalized greetings in different languages. Simple by design — this is about learning the pattern, not building something complex.

## Step 1: Scaffold the agent

From the workspace root:

```bash
uv run python -m agent_core.scaffold greeter --description "Personalized greetings in multiple languages"
```

This creates:

```
agents/greeter/
├── pyproject.toml
├── src/greeter/
│   ├── __init__.py
│   ├── config.py
│   └── tools.py
├── knowledge/
└── tests/
    └── __init__.py
```

Install the new package:

```bash
uv sync
```

## Step 2: Write the tools

Open `agents/greeter/src/greeter/tools.py` and replace the contents:

```python
"""Tools for the greeter agent."""

from typing import Annotated

from agent_framework import tool
from pydantic import Field

GREETINGS: dict[str, dict[str, str]] = {
    "dutch": {"hello": "Hallo", "goodbye": "Tot ziens", "thanks": "Dankjewel"},
    "japanese": {"hello": "こんにちは", "goodbye": "さようなら", "thanks": "ありがとう"},
    "spanish": {"hello": "Hola", "goodbye": "Adiós", "thanks": "Gracias"},
    "french": {"hello": "Bonjour", "goodbye": "Au revoir", "thanks": "Merci"},
}


@tool
def greet(
    language: Annotated[str, Field(description="Language: dutch, japanese, spanish, french")],
    phrase: Annotated[str, Field(description="Phrase type: hello, goodbye, thanks")],
) -> str:
    """Get a greeting in a specific language."""
    lang_data = GREETINGS.get(language.lower())
    if not lang_data:
        available = ", ".join(GREETINGS)
        return f"Language '{language}' not available. Try: {available}"
    result = lang_data.get(phrase.lower())
    if not result:
        return f"Unknown phrase '{phrase}'. Try: hello, goodbye, thanks"
    return f"{result} ({language}, {phrase})"


@tool
def list_languages() -> str:
    """List all available languages."""
    return ", ".join(GREETINGS)
```

### What's happening here

- **`@tool`** — registers the function so the AI model can call it
- **`Annotated[str, Field(description=...)]`** — tells the model what each parameter is for
- **Docstring** — the model reads this to decide _when_ to call the tool
- **Return type is `str`** — the model reads your return value as part of the conversation

## Step 3: Write the config

Open `agents/greeter/src/greeter/config.py` and replace:

```python
from agent_core import AgentConfig

config = AgentConfig(
    name="greeter-agent",
    description="Personalized greetings in multiple languages",
    instructions="""\
You are a greeting assistant.

Rules:
- Use the greet tool to look up greetings before answering.
- If a language isn't available, tell the user which languages are supported.
- Be friendly and concise.""",
    tools=["greet", "list_languages"],
    model="gpt-4.1-mini",
)
```

### Config fields explained

| Field | What it does |
|-------|-------------|
| `name` | Unique agent identifier — the router uses this |
| `description` | The triage agent reads this to decide routing. Be specific. |
| `instructions` | System prompt — defines the agent's behavior and rules |
| `tools` | List of function names from your `tools.py` |
| `model` | Azure OpenAI deployment name. Use `gpt-4.1-mini` for simple agents |

## Step 4: Verify the `__init__.py`

The scaffold already created the right exports, but verify `agents/greeter/src/greeter/__init__.py`:

```python
"""greeter agent."""
from . import tools
from .config import config

__all__ = ["config", "tools"]
```

This is the **plugin contract**: every agent must export `config` (an `AgentConfig`) and `tools` (the module).

## Step 5: Validate

```bash
uv run python -m agent_core.validate
```

You should see your greeter agent in the list with a checkmark. If not, check:
- Does `config.py` export a `config` variable?
- Does `tools.py` have functions matching the names in `config.tools`?
- Did you run `uv sync` after scaffolding?

## Step 6: Test the tools

Create `agents/greeter/tests/test_tools.py`:

```python
"""Tests for greeter agent tools."""

from greeter.tools import greet, list_languages


def test_greet_known_language():
    result = greet("dutch", "hello")
    assert "Hallo" in result


def test_greet_unknown_language():
    result = greet("klingon", "hello")
    assert "not available" in result


def test_greet_unknown_phrase():
    result = greet("french", "insult")
    assert "Unknown phrase" in result


def test_list_languages():
    result = list_languages()
    assert "dutch" in result
    assert "japanese" in result
```

Run:

```bash
uv run pytest agents/greeter/tests/ -v
```

## Step 7: Run the platform

```bash
uv run --package router-agent python -m router.main
```

Try these questions:

```
You > How do you say hello in Japanese?
You > List all available languages
You > My VPN is broken    # Routes to helpdesk-agent, not greeter
```

The triage agent reads your greeter agent's description and routes greeting questions to it automatically.

## What just happened?

1. You created a new Python package in `agents/greeter/`
2. The router auto-discovered it by scanning `agents/` at startup
3. Your `config.description` told the triage agent when to route to your agent
4. The AI model read your tool docstrings and called them when appropriate

## Next steps

- Study `helpdesk` — adds persistence (YAML KB, SQLite tickets) and HITL (`approval_mode`)
- Study `incident-triage` — adds structured output (Pydantic `response_format`)
- Study `infra-analyzer` — adds human-approved fixes (`@tool(approval_mode="always_require")`)
- [A2A demo](../examples/a2a-demo/) — connect agents across services
- [MCP server](../examples/mcp-server/) — expose tools via Model Context Protocol
