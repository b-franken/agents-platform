"""Evaluation: does the triage agent route to the correct specialist?

These tests require Azure credentials and make real API calls.
Run with: uv run pytest evals/ -m eval
"""

from __future__ import annotations

import pytest
from agent_framework.orchestrations import HandoffAgentUserRequest

pytestmark = pytest.mark.eval


ROUTING_CASES = [
    ("My VPN is not connecting, can you help?", "helpdesk-agent"),
    ("I need to create a support ticket for a printer issue", "helpdesk-agent"),
    ("How many employees are in the engineering department?", "data-analyst-agent"),
    ("Show me the total revenue by quarter", "data-analyst-agent"),
    ("Where can I find the company travel policy?", "knowledge-agent"),
    ("Search the documentation for onboarding procedures", "knowledge-agent"),
    ("The database is down and users cannot log in", "incident-triage-agent"),
    ("Review this Python code for security issues", "code-reviewer-agent"),
    ("Scan our Terraform configuration for best practice violations", "infra-analyzer-agent"),
]


@pytest.mark.parametrize("question,expected_agent", ROUTING_CASES)
async def test_triage_routes_correctly(
    workflow,
    question: str,
    expected_agent: str,
) -> None:
    """Verify triage hands off to the correct specialist."""
    agent_names: set[str] = set()
    async for event in workflow.run(question, stream=True):
        if hasattr(event, "executor_id") and event.executor_id:
            agent_names.add(event.executor_id)
        if event.type == "request_info" and isinstance(
            event.data, HandoffAgentUserRequest
        ):
            for msg in event.data.agent_response.messages:
                if hasattr(msg, "author_name"):
                    agent_names.add(msg.author_name)

    assert expected_agent in agent_names, (
        f"Expected {expected_agent} for '{question}', got agents: {agent_names}"
    )
