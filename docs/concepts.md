# Key Concepts

A guide to the core ideas behind this platform. If you're new to AI agents, start here.

## Multi-agent systems

A multi-agent system uses multiple specialized AI agents instead of one general-purpose chatbot. Each agent has a specific role, tools, and knowledge area.

**Why?** A single agent trying to do everything becomes unreliable. Specialized agents are more accurate because they have focused instructions and relevant tools. The triage agent routes questions to the right specialist — like a receptionist directing calls.

In this platform, the **router** agent discovers all specialists automatically and uses a HandoffBuilder workflow to manage routing.

## Azure AI Foundry

[Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/) is Microsoft's platform for building AI applications. It provides:

- **Model deployments** — host GPT-4.1, GPT-4.1-mini, and other models
- **Vector stores** — for RAG (document search)
- **Agent hosting** — run agents as managed services
- **Security** — Managed Identity, VNet isolation, content filtering

This platform uses Azure AI Foundry as its backend. Your agents run locally but call models and tools hosted in your Azure AI Foundry project.

## Microsoft Agent Framework

The [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) is the open-source framework this platform builds on. It provides:

- **Agent abstraction** — create agents with instructions, tools, and middleware
- **Workflows** — graph-based orchestration for multi-agent systems
- **HandoffBuilder** — purpose-built pattern for triage + specialist routing
- **Middleware** — intercept agent and tool calls (logging, validation, termination)
- **Checkpointing** — save and resume workflow state

The Agent Framework is the successor to both AutoGen and Semantic Kernel, combining the simplicity of AutoGen with the enterprise features of Semantic Kernel.

## HandoffBuilder orchestration

HandoffBuilder is the orchestration pattern used by the router:

```
User → Triage Agent → Specialist A → Triage Agent → User
                    → Specialist B → Triage Agent → User
```

- **Bidirectional handoffs** — specialists can hand back to triage
- **Conversation history** — preserved across all handoffs
- **Autonomous mode** — triage can route without pausing for user input
- **Checkpointing** — the entire workflow state can be saved and resumed

This is different from simple function calling. The triage agent maintains context and can route follow-up questions to the same or different specialists.

## A2A Protocol (Agent-to-Agent)

The [A2A protocol](https://a2a-protocol.org/) is an open standard (Linux Foundation) for agents to communicate across frameworks and services. It defines:

- **Agent Cards** — standardized capability declarations (served at `/.well-known/agent-card.json`)
- **Task model** — asynchronous, long-running operations with streaming
- **Discovery** — agents find each other via well-known URLs

**Why it matters:** With A2A, a Python agent on this platform can call a Java agent running on Google ADK, or a C# agent on another Azure service. No custom integration code needed.

This platform supports A2A natively. Remote agents are configured via:

```
A2A_AGENTS=legal=https://legal.internal/a2a,finance=https://finance.internal/a2a
```

They appear in routing alongside local agents — the triage agent doesn't distinguish between local and remote.

## MCP (Model Context Protocol)

[MCP](https://modelcontextprotocol.io/) is a standard (by Anthropic) for connecting AI agents to external tools and data sources. While A2A is agent-to-agent, MCP is agent-to-tool.

In this platform, MCP tools are configured in your agent's config:

```python
config = AgentConfig(
    tools=[
        "local_function",
        "mcp:confluence:http://localhost:3000/mcp",
        "mcp:jira:http://localhost:3001/mcp",
    ],
)
```

The platform resolves `mcp:` prefixed tools automatically. No wrapper code needed.

## RAG (Retrieval-Augmented Generation)

RAG means giving your agent access to your own documents. Instead of relying only on the model's training data, the agent searches your documents for relevant information.

In this platform:

1. Drop documents in `agents/my-agent/knowledge/` (PDF, MD, DOCX, etc.)
2. Upload to Azure vector store: `uv run python -m agent_core.knowledge upload`
3. Set `file_search_enabled=True` in your config

The agent can now search your documents and include citations in its responses.

## Human-in-the-loop (HITL)

Some operations are too sensitive for an AI agent to execute autonomously. Human-in-the-loop means the agent pauses and asks for human approval before proceeding.

In this platform, it's one decorator:

```python
@tool(approval_mode="always_require")
def create_ticket(title: str, priority: str) -> str:
    """Create a support ticket. Requires human approval."""
    ...
```

When the agent tries to call this tool, the workflow pauses, shows the parameters to the user, and waits for approval. No custom state machine needed.

## Middleware

Middleware intercepts agent and tool calls before and after execution. This platform has three middleware layers:

1. **InputGuard** — rejects inputs that are too long or exceed conversation turn limits
2. **LoggingAgent** — logs agent invocations with timing
3. **LoggingFunction** — logs tool calls with sensitive data masking

Middleware can terminate execution early (e.g., InputGuard blocking oversized input) — a capability not found in most other frameworks.
