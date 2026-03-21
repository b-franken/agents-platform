"""Shared fixtures for agent evaluation tests."""

from __future__ import annotations

import pytest
from agent_core.factory import create_client
from router.config import TRIAGE_INSTRUCTIONS, build_registry


@pytest.fixture(scope="session")
def registry():
    return build_registry()


@pytest.fixture(scope="session")
def client():
    return create_client()


@pytest.fixture(scope="session")
def workflow(registry, client):
    triage = client.as_agent(
        name="triage",
        instructions=TRIAGE_INSTRUCTIONS.format(agents=registry.describe_agents()),
        description="Routes questions to the right specialist",
    )
    return registry.build_handoff_workflow(client=client, triage_agent=triage)
