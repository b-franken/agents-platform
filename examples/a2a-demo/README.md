# A2A Cross-Framework Demo

This demo shows two independent agent services communicating via the [A2A protocol](https://a2a-protocol.org/) — the open standard for agent-to-agent communication.

**This is unique.** No other open-source agent hub demonstrates A2A end-to-end with Microsoft Agent Framework.

## What it demonstrates

1. **Agent Card discovery** — Service A publishes its capabilities at `/.well-known/agent-card.json`
2. **Cross-service routing** — the triage agent routes to a remote agent as seamlessly as a local one
3. **A2A protocol in action** — standardized communication between two separate processes

## Architecture

```
┌────────────────────────────────────────────────┐
│ Agent Platform (Service B)                     │
│                                                │
│  User → Triage → Helpdesk (local)              │
│                → Knowledge (local)             │
│                → Data Analyst (local)           │
│                → Legal Advisor (remote, A2A) ──┼──→ Service A
└────────────────────────────────────────────────┘     (port 9000)
```

## Prerequisites

- A working Agent Platform setup ([Getting Started](../../docs/getting-started.md))
- Azure AI Foundry credentials configured (both services need them — the Legal Advisor uses Azure OpenAI for reasoning)

## Run the demo

### Step 1: Start the Legal Advisor service (Service A)

In a new terminal:

```bash
cd examples/a2a-demo
pip install uv  # if not already installed
uv sync
uv run python service_a/main.py
```

You should see:

```
Legal Advisor A2A server running on http://localhost:9000
Agent Card: http://localhost:9000/.well-known/agent-card.json
```

### Step 2: Configure the platform to connect

Add to your `.env` file (in the workspace root):

```
A2A_AGENTS=legal=http://localhost:9000/a2a
```

### Step 3: Start the platform (Service B)

In another terminal:

```bash
uv run --package router-agent python -m router.main
```

You should see `legal` listed as a discovered agent (marked as remote/A2A).

### Step 4: Test it

```
You > Is our data processing compliant with GDPR?
────────────────────
Triage → Legal Advisor (A2A)
Legal Advisor: Based on a compliance check, here are the key GDPR considerations...
```

The triage agent routes legal questions to the remote Legal Advisor via A2A, while technical questions still go to the local helpdesk agent.

## How it works

1. **Service A** runs a standalone A2A-compatible agent server on port 9000 (with real Azure OpenAI reasoning)
2. **Service B** (the platform) reads `A2A_AGENTS=legal=http://localhost:9000/a2a` from `.env`
3. The router's `register_a2a_agents()` creates an `A2AAgent` connection
4. The triage agent sees the legal agent alongside local agents and routes accordingly
5. Communication happens over the A2A protocol — standardized, framework-agnostic

## Docker (optional)

Run both services together:

```bash
cd examples/a2a-demo
docker compose up
```

## Files

```
examples/a2a-demo/
├── README.md              # This file
├── pyproject.toml         # Dependencies for Service A
├── docker-compose.yaml    # Run both services together
└── service_a/
    ├── main.py            # Legal Advisor A2A server (real agent reasoning)
    └── tools.py           # Legal tools (compliance checks, contract reviews)
```

## Why A2A matters

Without A2A, connecting agents across services requires custom REST APIs, manual capability documentation, and ad-hoc async handling. A2A standardizes all of this:

- **Agent Cards** replace API docs
- **Task model** replaces custom async patterns
- **Streaming** replaces polling
- **Any framework** can participate (Python, C#, Java, Go)

See [Key Concepts: A2A Protocol](../../docs/concepts.md#a2a-protocol-agent-to-agent) for more background.
