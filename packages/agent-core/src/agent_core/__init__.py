"""Shared library for the agent platform."""

__all__ = [
    "AgentConfig",
    "AgentRegistry",
    "create_agent_from_config",
    "create_client",
]

from .config import AgentConfig
from .factory import create_agent_from_config, create_client
from .registry import AgentRegistry
