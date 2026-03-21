"""Evaluation: does each specialist agent select the right tool?

These tests require Azure credentials and make real API calls.
Run with: uv run pytest evals/ -m eval
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from agent_framework import FunctionInvocationContext, FunctionMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

pytestmark = pytest.mark.eval


class ToolTracker(FunctionMiddleware):
    """Records which tools were called during an agent run."""

    def __init__(self) -> None:
        self.called: list[str] = []

    async def process(
        self,
        context: FunctionInvocationContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        self.called.append(context.function.name)
        await call_next()


TOOL_CASES = [
    ("helpdesk-agent", "My VPN keeps disconnecting", "search_knowledge_base"),
    ("data-analyst-agent", "What tables are available?", "describe_tables"),
    ("data-analyst-agent", "How many employees are in engineering?", "run_sql"),
    (
        "knowledge-agent",
        "Search for information about remote work in the handbook",
        "search_documents",
    ),
    (
        "incident-triage-agent",
        "The production database is completely down",
        "classify_incident",
    ),
    (
        "incident-triage-agent",
        "Show me the runbook for a network outage",
        "get_runbook",
    ),
    (
        "code-reviewer-agent",
        "Check this code: import os; eval(input())",
        "check_security_patterns",
    ),
    (
        "infra-analyzer-agent",
        'Scan this: resource "azurerm_storage_account" "s" {}',
        "scan_terraform",
    ),
]


@pytest.mark.parametrize("agent_name,question,expected_tool", TOOL_CASES)
async def test_agent_selects_correct_tool(
    registry,
    client,
    agent_name: str,
    question: str,
    expected_tool: str,
) -> None:
    """Verify that a specialist agent calls the expected tool for a given question."""
    tracker = ToolTracker()
    entry = registry.get(agent_name)
    agent = entry.get_or_create(client)

    await agent.run(question, middleware=[tracker])

    assert expected_tool in tracker.called, (
        f"Expected tool '{expected_tool}' for '{question}', got: {tracker.called}"
    )
