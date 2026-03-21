"""Agent registry — register, discover and orchestrate agents."""

from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from agent_framework.a2a import A2AAgent
from agent_framework.orchestrations import HandoffBuilder

from .factory import create_agent_from_config

if TYPE_CHECKING:
    from types import ModuleType

    from agent_framework import Agent, CheckpointStorage, Workflow
    from agent_framework.azure import AzureOpenAIResponsesClient

    from .config import AgentConfig

__all__ = ["AgentRegistry", "RegisteredAgent"]

logger = logging.getLogger(__name__)


@dataclass
class RegisteredAgent:
    """An agent registered in the platform."""

    config: AgentConfig
    tools_module: ModuleType
    _agent: Agent | None = field(default=None, repr=False)
    _client: AzureOpenAIResponsesClient | None = field(
        default=None,
        repr=False,
    )

    def get_or_create(
        self,
        client: AzureOpenAIResponsesClient | None = None,
    ) -> Agent:
        """Lazily create the agent on first access."""
        if self._agent is None:
            self._agent, self._client = create_agent_from_config(
                self.config,
                self.tools_module,
                client,
            )
        return self._agent


class AgentRegistry:
    """Registry for local and remote (A2A) agents."""

    def __init__(self) -> None:
        self._agents: dict[str, RegisteredAgent] = {}
        self._remote_agents: dict[str, A2AAgent] = {}
        self._exit_stack = AsyncExitStack()

    # -- Local agents ------------------------------------------------

    def register(
        self,
        config: AgentConfig,
        tools_module: ModuleType,
    ) -> None:
        if config.name in self._agents:
            msg = f"Agent '{config.name}' already registered"
            raise ValueError(msg)
        self._agents[config.name] = RegisteredAgent(
            config=config,
            tools_module=tools_module,
        )
        logger.info(
            "Registered agent: %s — %s",
            config.name,
            config.description,
        )

    def get(self, name: str) -> RegisteredAgent:
        try:
            return self._agents[name]
        except KeyError:
            available = ", ".join(self._agents)
            msg = f"Agent '{name}' not found. Available: {available}"
            raise KeyError(msg) from None

    def list_agents(self) -> list[RegisteredAgent]:
        return list(self._agents.values())

    # -- Remote A2A agents -------------------------------------------

    async def register_remote(
        self,
        name: str,
        url: str,
        *,
        description: str = "",
    ) -> None:
        """Register a remote agent via the A2A protocol.

        The A2AAgent is opened immediately and kept alive until
        ``close()`` is called.
        """
        if name in self._remote_agents:
            msg = f"Remote agent '{name}' already registered"
            raise ValueError(msg)
        agent = A2AAgent(name=name, url=url)
        await self._exit_stack.enter_async_context(agent)
        self._remote_agents[name] = agent
        logger.info("Remote A2A agent: %s → %s", name, url)

    async def close(self) -> None:
        """Close all remote A2A agent connections."""
        await self._exit_stack.aclose()
        self._remote_agents.clear()

    # -- Description (used by triage system prompt) ------------------

    def describe_agents(self) -> str:
        """Human-readable list of all agents."""
        lines = [
            f"- {e.config.name}: {e.config.description}" for e in self._agents.values()
        ]
        for name, agent in self._remote_agents.items():
            desc = getattr(agent, "description", "remote A2A agent")
            lines.append(f"- {name}: {desc} (remote)")
        return "\n".join(lines)

    # -- Workflow building -------------------------------------------

    def build_handoff_workflow(
        self,
        client: AzureOpenAIResponsesClient,
        triage_agent: Agent,
        *,
        workflow_name: str = "internal_platform",
        autonomous_triage: bool = True,
        checkpoint_storage: CheckpointStorage | None = None,
    ) -> Workflow:
        """Build a HandoffBuilder workflow.

        Includes both local specialist agents and remote A2A
        agents as participants.
        """
        local = [entry.get_or_create(client) for entry in self._agents.values()]
        remote = list(self._remote_agents.values())
        all_specialists: list[Agent] = [*local, *remote]

        builder = (
            HandoffBuilder(
                name=workflow_name,
                participants=[triage_agent, *all_specialists],
                checkpoint_storage=checkpoint_storage,
            )
            .with_start_agent(triage_agent)
            .add_handoff(triage_agent, all_specialists)
        )

        for specialist in all_specialists:
            builder = builder.add_handoff(
                specialist,
                [triage_agent],
            )

        if autonomous_triage:
            builder = builder.with_autonomous_mode(
                agents=[triage_agent],
            )

        return builder.build()

    # -- Dunder helpers ----------------------------------------------

    def __len__(self) -> int:
        return len(self._agents) + len(self._remote_agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents or name in self._remote_agents
