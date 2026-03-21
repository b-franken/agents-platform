"""Tests for AgentConfig — defaults, YAML loading, frozen immutability."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
from agent_core import AgentConfig


class TestAgentConfig:
    def test_defaults(self) -> None:
        cfg = AgentConfig(name="test", instructions="Test")
        assert cfg.model == "gpt-4.1"
        assert cfg.max_input_length == 4000
        assert cfg.max_conversation_turns == 50
        assert cfg.timeout_seconds == 30
        assert cfg.max_output_tokens == 2048
        assert cfg.file_search_enabled is False
        assert cfg.tools == []
        assert cfg.description == ""

    def test_frozen(self) -> None:
        cfg = AgentConfig(name="test", instructions="Test")
        with pytest.raises(AttributeError):
            cfg.name = "changed"  # type: ignore[misc]

    def test_custom_values(self) -> None:
        cfg = AgentConfig(
            name="custom",
            instructions="Custom agent",
            description="A custom agent",
            model="gpt-4.1-mini",
            tools=["tool_a", "tool_b"],
            max_input_length=1000,
        )
        assert cfg.model == "gpt-4.1-mini"
        assert cfg.tools == ["tool_a", "tool_b"]
        assert cfg.max_input_length == 1000

    def test_from_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text(
            "name: yaml-agent\n"
            "instructions: You are helpful.\n"
            "description: YAML test agent\n"
            "model: gpt-4.1-mini\n"
            "tools:\n"
            "  - search_docs\n"
        )
        cfg = AgentConfig.from_yaml(yaml_file)
        assert cfg.name == "yaml-agent"
        assert cfg.model == "gpt-4.1-mini"
        assert cfg.tools == ["search_docs"]
        assert cfg.description == "YAML test agent"
