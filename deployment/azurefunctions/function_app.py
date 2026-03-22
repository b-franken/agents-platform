"""Azure Functions deployment for the agent platform.

Exposes the HandoffBuilder workflow as durable Azure Functions
with automatic HTTP endpoints and state persistence.

Setup:
    pip install -r requirements.txt
    func start

Docs: https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions
"""

from __future__ import annotations

from agent_core.factory import create_client
from agent_framework.azure import AgentFunctionApp
from dotenv import load_dotenv
from router.config import TRIAGE_INSTRUCTIONS, build_registry

load_dotenv()

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

app = AgentFunctionApp(workflow=workflow, enable_health_check=True)
