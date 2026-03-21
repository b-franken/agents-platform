"""Evaluation: does the agent response contain relevant information?

These tests require Azure credentials and make real API calls.
Run with: uv run pytest evals/ -m eval
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.eval


QUALITY_CASES = [
    (
        "helpdesk-agent",
        "My VPN is not connecting, what should I do?",
        ["vpn", "connect"],
    ),
    (
        "knowledge-agent",
        "Search for documents about security policies",
        ["security", "policy"],
    ),
    (
        "data-analyst-agent",
        "Describe the available database tables",
        ["table", "integer"],
    ),
    (
        "incident-triage-agent",
        "Our main API is returning 500 errors for all users",
        ["severity", "runbook"],
    ),
    (
        "code-reviewer-agent",
        "Review this code for issues: def f(x=[]): x.append(1)",
        ["mutable", "default"],
    ),
    (
        "infra-analyzer-agent",
        "Scan this Terraform: resource"
        ' "azurerm_storage_account" "main"'
        ' { name = "test" }',
        ["encryption", "tag"],
    ),
]


@pytest.mark.parametrize("agent_name,question,expected_keywords", QUALITY_CASES)
async def test_response_contains_relevant_info(
    registry,
    client,
    agent_name: str,
    question: str,
    expected_keywords: list[str],
) -> None:
    """Verify that agent responses contain expected factual content."""
    entry = registry.get(agent_name)
    agent = entry.get_or_create(client)

    response = await agent.run(question)

    full_text = " ".join(
        msg.text.lower()
        for msg in response.messages
        if hasattr(msg, "text") and msg.text
    )

    missing = [kw for kw in expected_keywords if kw not in full_text]
    assert not missing, (
        f"Missing {missing} for '{question}'. Response: {full_text[:500]}"
    )
