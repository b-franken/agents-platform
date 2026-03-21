# Getting Started

## Prerequisites

- **Python 3.13+** — [download](https://www.python.org/downloads/)
- **uv** package manager — [install](https://docs.astral.sh/uv/) or `pip install uv`
- **Azure subscription** with [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/) — [free trial](https://azure.microsoft.com/free/)
- **Azure CLI** — [install](https://learn.microsoft.com/cli/azure/install-azure-cli)

## Option 1: GitHub Codespaces (fastest)

Click "Open in Codespaces" from the repository. Everything is pre-configured — skip to [Configure Azure](#configure-azure).

## Option 2: Local setup

```bash
git clone https://github.com/b-franken/agent-platform.git
cd agent-platform
pip install uv
uv sync
```

**What just happened?** `uv sync` installed all dependencies and registered the workspace packages (agent-core + all agents) as editable installs.

## Configure Azure

You need an Azure AI Foundry project with a model deployment.

### Option A: Use an existing AI Foundry project

1. Log in:
   ```bash
   az login
   ```

2. Copy your project endpoint and deployment name to `.env`:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```
   AZURE_AI_PROJECT_ENDPOINT=https://your-account.services.ai.azure.com/api/projects/your-project-id
   AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4.1
   ```

### Option B: Deploy new infrastructure with Terraform

```bash
az login
cd infra
terraform init
terraform apply -var-file=environments/poc.tfvars
```

Copy the output:
```bash
terraform output project_endpoint
# Paste this value into .env as AZURE_AI_PROJECT_ENDPOINT
```

## Verify your setup

Run the pre-flight check:

```bash
uv run python scripts/preflight.py
```

You should see:

```
============================================================
Agent Platform — Pre-flight Check
============================================================

[1/3] Python packages: OK
[2/3] Environment variables: OK
[3/3] Azure authentication: OK

READY — All checks passed!
```

If any check fails, see [Troubleshooting](troubleshooting.md).

## Run

```bash
# Validate all agents
uv run python -m agent_core.validate

# Start the platform
uv run --package router-agent python -m router.main
```

You should see:

```
============================================================
Agent Platform (7 agents)
- code-reviewer-agent: Code review demo — regex-based quality and security pattern scanning
- data-analyst-agent: Queries company data: employees, projects, tickets.
- expense-approver: Expense submissions, budget checks, and spending approvals
- helpdesk-agent: IT helpdesk: troubleshoots problems using a knowledge base
- incident-triage-agent: Incident triage demo — keyword-based severity classification
- infra-analyzer-agent: Infrastructure analysis demo — Terraform pattern scanning
- knowledge-agent: Searches company documentation: handbook, policies, procedures
============================================================
You >
```

**What just happened?** The router scanned `agents/`, found seven specialist agents, read their descriptions, and built a HandoffBuilder workflow with bidirectional handoffs.

## Example conversation

```
You > My VPN won't connect, I keep getting error 809
────────────────────
helpdesk-agent: Error 809 typically means the VPN ports are blocked.
Try these steps: 1) Check your firewall settings ...
────────────────────
You > How many open tickets does the engineering team have?
────────────────────
data-analyst-agent: The engineering team currently has 12 open tickets.
Here's the breakdown by priority: ...
```

The triage agent reads the `description` field of each agent config to decide where to route each question.

## Next steps

- [Tutorial: Build Your First Agent](tutorial.md) — step-by-step from zero
- [Key Concepts](concepts.md) — understand multi-agent systems, A2A, MCP, RAG
- [Add your own agent](adding-agents.md) — the full plugin contract
- [Deploy to Azure](deployment.md) — Docker, azd, Terraform, Azure Functions
- [Architecture](architecture.md) — how it all works under the hood
