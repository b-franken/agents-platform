# Architecture

## Overview

The Agent Platform is a multi-agent orchestration system built on [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) and [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/).

```
User Input
    │
    ▼
┌──────────────────┐
│   Triage Agent   │  ← Routes questions to the right specialist
│   (Router)       │
└────────┬─────────┘
         │ HandoffBuilder
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Agent A │ │Agent B │  ← Specialist agents with domain-specific tools
│(tools) │ │(tools) │
└────────┘ └────────┘
```

## Core components

### agent-core (shared library)

Located in `packages/agent-core/`. Provides:

| Component | File | Purpose |
|-----------|------|---------|
| `AgentConfig` | `config.py` | Standardized agent configuration |
| `create_client()` | `factory.py` | Azure OpenAI client with explicit auth |
| `create_agent_from_config()` | `factory.py` | Agent creation with middleware |
| `AgentRegistry` | `registry.py` | Agent discovery and HandoffBuilder workflow |
| Middleware | `middleware.py` | InputGuard, logging, sensitive data masking |
| Scaffold CLI | `scaffold.py` | Generate new agent packages |
| Validate CLI | `validate.py` | Check all agents before startup |

### Router

Located in `agents/router/`. Auto-discovers all agents in `agents/` and creates a triage workflow using HandoffBuilder. The triage agent reads each agent's `description` to decide routing.

### Specialist agents

Each agent is a Python package in `agents/` that exports `config` and `tools`. See [Adding Agents](adding-agents.md).

## Authentication

Explicit credential selection in `factory.py` — no fallback chains:

| Environment variable | Auth method |
|---------------------|-------------|
| `AZURE_OPENAI_API_KEY` set | API key |
| `AZURE_CLIENT_ID` set | Managed Identity (production) |
| Neither | AzureCliCredential (development) |

## Tool resolution

Tools in an agent's config are resolved at startup:

- `"function_name"` → looked up in the agent's tools module
- `"mcp:name:url"` → resolved via MCP protocol to an external tool server
- `file_search_enabled=True` → Azure vector store file search tool

## Middleware stack

Every agent gets three middleware layers:

1. **InputGuard** — enforces `max_input_length` and `max_conversation_turns`
2. **LoggingAgent** — logs agent invocations and handoffs
3. **LoggingFunction** — logs tool calls with sensitive data masking

## Checkpointing

The platform uses `FileCheckpointStorage` to persist workflow state. Conversations can be resumed after interruption with `--resume`.

## Deployment options

| Method | Use case |
|--------|----------|
| CLI (`python -m router.main`) | Local development |
| DevUI (`uv run devui`) | Browser-based testing |
| Docker Compose | Container-based development |
| Foundry Agent Service | Production — managed runtime, token-only cost (default) |
| Azure Container Apps | Production — self-hosted alternative |
| Azure Functions | Serverless production |

### Foundry hosted vs. Container Apps

The default deployment uses **Azure AI Foundry Agent Service** (GA March 2026). This is Microsoft's recommended path: prototype locally with Agent Framework, then deploy to Foundry for production.

```
Local (uv run) → Foundry hosted (azd up)          # recommended
               → Container Apps (deployment_mode)  # alternative
```

Foundry hosted deploys your Agent Framework code as a container that Foundry manages. It provisions Cosmos DB (thread storage), AI Search (vector store), and Storage Account (files) automatically via the `create_byor` flag in the AVM module.
