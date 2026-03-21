# AGENTS.md

## Project Overview

Multi-agent platform built on [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/) with Azure AI Foundry. Agents communicate via HandoffBuilder orchestration and A2A protocol.

## Setup

```bash
uv sync
cp .env.example .env
# Set AZURE_AI_PROJECT_ENDPOINT and AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME
```

## Build & Test

```bash
# Unit tests (no Azure credentials needed)
uv run pytest tests/ agents/*/tests/ -v

# Evals (requires Azure credentials + az login)
uv run pytest evals/ -m eval -v

# Lint + type check
uv run ruff check .
uv run mypy packages/agent-core/src/
```

## Run

```bash
# Interactive router (all agents)
uv run --package router-agent python -m router.main

# Single agent scaffold
uv run python -m agent_core.scaffold my-new-agent
```

## Code Style

- Python 3.13+, type annotations everywhere
- `Annotated[str, Field(description=...)]` for tool parameters
- `@tool` decorator from `agent_framework` (not raw functions)
- `@tool(approval_mode="always_require")` for destructive operations
- Pydantic `BaseModel` for structured output, `dataclass(frozen=True)` for configs
- No `# type: ignore`, no `Any` dodges, no bare `except Exception`

## Agent Structure

Each agent lives in `agents/<name>/` with:
```
agents/<name>/
  pyproject.toml          # workspace package
  src/<package>/
    __init__.py           # exports config + tools
    config.py             # AgentConfig instance
    tools.py              # @tool-decorated functions
  tests/
    __init__.py
    test_tools.py
```

Auto-discovered by `AgentRegistry` at startup via `agents/*/src/*/config.py`.

## PR Instructions

- Run `uv run pytest tests/ agents/*/tests/` before submitting
- Run `uv run ruff check .` — zero warnings
- New agents: use `uv run python -m agent_core.scaffold <name>`
- New tools: add unit tests in `agents/<name>/tests/test_tools.py`
