"""Router configuration — auto-discovers local and remote agents."""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path

from agent_core import AgentRegistry

logger = logging.getLogger(__name__)

TRIAGE_INSTRUCTIONS: str = """\
You are the triage agent for the company's internal AI platform.

Your ONLY job is to route user questions to the right specialist agent.
Analyse the user's question and ALWAYS hand off to the most relevant agent.

If no specialist matches, say what agents are available and what they handle.

Available agents:
{agents}
"""


def build_registry() -> AgentRegistry:
    """Auto-discover and register all local specialist agents.

    Convention: each agent package in agents/ must export
    ``config`` and ``tools`` from its __init__.py.
    """
    registry = AgentRegistry()
    agents_dir = Path(__file__).resolve().parents[4] / "agents"

    for child in sorted(agents_dir.iterdir()):
        if not child.is_dir() or child.name == "router":
            continue
        package_name = child.name.replace("-", "_")
        try:
            module = importlib.import_module(package_name)
        except ImportError:
            logger.warning(
                "Skipping %s — not installed (run `uv sync`)",
                child.name,
            )
            continue

        config = getattr(module, "config", None)
        tools = getattr(module, "tools", None)

        if config is None or tools is None:
            logger.warning(
                "Skipping %s — no `config`/`tools` export",
                child.name,
            )
            continue

        registry.register(config, tools)

    return registry


async def register_a2a_agents(registry: AgentRegistry) -> None:
    """Register remote A2A agents from the A2A_AGENTS env var.

    Format: ``name=url,name=url``

    Example::

        A2A_AGENTS=legal=https://legal.internal/a2a,finance=https://finance.internal/a2a
    """
    raw = os.getenv("A2A_AGENTS", "")
    if not raw.strip():
        return

    for entry in raw.split(","):
        entry = entry.strip()
        if "=" not in entry:
            logger.warning("Invalid A2A_AGENTS entry: %s", entry)
            continue
        name, url = entry.split("=", 1)
        await registry.register_remote(
            name=name.strip(),
            url=url.strip(),
        )
