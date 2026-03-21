"""Agent configuration dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["AgentConfig"]


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Configuration for a single agent. Instantiate per use case or load from YAML."""

    name: str
    instructions: str
    description: str = ""
    tools: list[str] = field(default_factory=list)
    file_search_enabled: bool = False
    model: str = "gpt-4.1"
    max_output_tokens: int = 2048
    max_conversation_turns: int = 50
    max_input_length: int = 4000
    timeout_seconds: int = 30

    @classmethod
    def from_yaml(cls, path: str | Path) -> AgentConfig:
        """Load agent configuration from a YAML file.

        Example YAML:
            name: my-agent
            description: Handles customer questions
            model: gpt-4.1
            instructions: |
              You are a helpful assistant...
            tools:
              - search_knowledge_base
              - mcp:confluence:http://localhost:3000/mcp
        """
        import yaml  # lazy import — only needed when using YAML

        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(**data)
