"""Legal Advisor — A2A agent server using the official A2A SDK.

Exposes a Legal Advisor agent via the A2A protocol. The Agent Platform
can discover and route to this agent using the A2A_AGENTS env var.

Usage::

    uv run python service_a/main.py
    # Agent Card at http://localhost:9000/.well-known/agent-card.json

Requires:
    Azure AI Foundry credentials (same as the main platform).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils.message import new_agent_text_message
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

if TYPE_CHECKING:
    from a2a.server.events import EventQueue
    from agent_framework import Agent

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PORT = int(os.getenv("A2A_PORT", "9000"))

DESCRIPTION = (
    "Compliance checks (GDPR, SOX, PCI-DSS, HIPAA) and "
    "contract template reviews (NDA, SLA, DPA, MSA)"
)


class LegalAdvisorExecutor(AgentExecutor):
    """Runs the Legal Advisor agent for incoming A2A requests."""

    def __init__(self, agent: Agent, client: AzureOpenAIResponsesClient) -> None:
        self._agent = agent
        self._client = client

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        logger.info("A2A request: %s", user_input[:100])
        response = await self._agent.run(user_input)
        await event_queue.enqueue_event(
            new_agent_text_message(response.text or "(no response)")
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError


def _create_agent() -> tuple[Agent, AzureOpenAIResponsesClient]:
    """Create the Legal Advisor agent with Azure OpenAI."""
    from tools import check_compliance, review_contract

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    deployment_name = os.getenv(
        "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME",
        "gpt-4.1-mini",
    )

    if api_key:
        client = AzureOpenAIResponsesClient(
            deployment_name=deployment_name,
            api_key=api_key,
        )
    elif endpoint:
        endpoint_key = (
            "project_endpoint" if "/api/projects/" in endpoint else "endpoint"
        )
        client = AzureOpenAIResponsesClient(
            deployment_name=deployment_name,
            credential=AzureCliCredential(),
            **{endpoint_key: endpoint},
        )
    else:
        msg = "Set AZURE_AI_PROJECT_ENDPOINT or AZURE_OPENAI_API_KEY in .env"
        raise RuntimeError(msg)

    agent = client.as_agent(
        name="Legal Advisor",
        description=DESCRIPTION,
        instructions=(
            "You are a legal advisor. Use your tools to answer "
            "questions about compliance and contracts. "
            "Be concise and factual."
        ),
        tools=[check_compliance, review_contract],
    )
    return agent, client


def main() -> None:
    load_dotenv()

    logger.info("Initializing Legal Advisor agent...")
    agent, client = _create_agent()
    logger.info("Agent ready (using Azure OpenAI)")

    agent_card = AgentCard(
        name="Legal Advisor",
        description=DESCRIPTION,
        url=f"http://localhost:{PORT}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="check_compliance",
                name="Compliance Check",
                description="Check compliance status for GDPR, SOX, PCI-DSS, HIPAA",
                tags=["compliance", "regulation"],
                examples=["Are we GDPR compliant?", "Check SOX status"],
            ),
            AgentSkill(
                id="review_contract",
                name="Contract Review",
                description="Review contract templates (NDA, SLA, DPA, MSA)",
                tags=["contracts", "legal"],
                examples=["Review the NDA template", "What's in our SLA?"],
            ),
        ],
    )

    handler = DefaultRequestHandler(
        agent_executor=LegalAdvisorExecutor(agent, client),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler,
    )

    logger.info("Legal Advisor A2A server on http://localhost:%d", PORT)
    logger.info("Agent Card: http://localhost:%d/.well-known/agent-card.json", PORT)
    uvicorn.run(server.build(), host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
