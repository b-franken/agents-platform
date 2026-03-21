"""Azure Functions deployment for the agent platform.

Provides durable HTTP endpoints for the HandoffBuilder workflow:
    POST /api/workflow/run           — start a conversation
    GET  /api/workflow/status/{id}   — check status
    POST /api/workflow/respond/...   — HITL response

Setup:
    pip install agent-framework-azurefunctions --pre
    func start

Docs: https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions
"""

from __future__ import annotations

from agent_core.factory import create_client
from agent_framework.azurefunctions import AgentFunctionApp
from dotenv import load_dotenv
from router.config import TRIAGE_INSTRUCTIONS, build_registry

load_dotenv()

# Build the workflow
registry = build_registry()
client = create_client()

triage = client.as_agent(
    name="triage",
    instructions=TRIAGE_INSTRUCTIONS.format(
        agents=registry.describe_agents(),
    ),
    description="Routes questions to the right specialist",
)

workflow = registry.build_handoff_workflow(
    client=client,
    triage_agent=triage,
)

# Register with Azure Functions
app = AgentFunctionApp(workflow=workflow)
