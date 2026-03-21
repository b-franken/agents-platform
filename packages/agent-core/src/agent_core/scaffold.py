"""Scaffold a new agent in the workspace.

Usage::

    uv run python -m agent_core.scaffold <name>
    uv run python -m agent_core.scaffold <name> -d "desc"
    uv run python -m agent_core.scaffold <name> -m gpt-4.1-mini
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _to_snake(name: str) -> str:
    """Convert kebab-case agent name to snake_case package name."""
    return name.replace("-", "_")


def _find_agents_dir() -> Path:
    """Find the agents/ directory in the workspace root."""
    candidate = Path.cwd() / "agents"
    if candidate.is_dir():
        return candidate
    msg = "Could not find agents/ directory. Run this command from the workspace root."
    raise FileNotFoundError(msg)


_PYPROJECT_TEMPLATE = """\
[project]
name = "{name}"
version = "0.1.0"
description = "{description}"
requires-python = ">=3.13"
dependencies = ["agent-core"]

[tool.uv.sources]
agent-core = {{ workspace = true }}

[tool.hatch.build.targets.wheel]
packages = ["src/{package}"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""

_INIT_TEMPLATE = """\
\"\"\"{name} agent.\"\"\"\

from . import tools
from .config import config

__all__ = ["config", "tools"]
"""

_CONFIG_TEMPLATE = """\
\"\"\"Agent configuration.\"\"\"\

from agent_core import AgentConfig

config = AgentConfig(
    name="{name}",
    description="{description}",
    instructions=\"\"\"You are a helpful assistant for {description_lower}.

Rules:
- Use your tools to look up information before answering.
- Be concise and factual.
- If you don't know something, say so.
\"\"\",
    tools=[\"example_tool\"],
    file_search_enabled=False,
    model="{model}",
)
"""

_TOOLS_TEMPLATE = """\
\"\"\"Tools for the {name} agent.\"\"\"

from agent_framework import tool


@tool
def example_tool(query: str) -> str:
    \"\"\"Example tool — replace with your own implementation.\"\"\"
    return f"TODO: implement tool logic for: {{query}}"
"""

_TEST_INIT = """\
\"\"\"Tests for {package}.\"\"\"\
"""


def scaffold(name: str, description: str, model: str) -> Path:
    """Create a new agent directory with all required files."""
    agents_dir = _find_agents_dir()
    agent_dir = agents_dir / name
    package = _to_snake(name)

    if agent_dir.exists():
        msg = f"Directory already exists: {agent_dir}"
        raise FileExistsError(msg)

    # Create directory structure
    src_dir = agent_dir / "src" / package
    knowledge_dir = agent_dir / "knowledge"
    tests_dir = agent_dir / "tests"

    src_dir.mkdir(parents=True)
    knowledge_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    # Write files
    (agent_dir / "pyproject.toml").write_text(
        _PYPROJECT_TEMPLATE.format(
            name=name,
            description=description,
            package=package,
        )
    )
    (src_dir / "__init__.py").write_text(_INIT_TEMPLATE.format(name=package))
    (src_dir / "config.py").write_text(
        _CONFIG_TEMPLATE.format(
            name=name,
            description=description,
            description_lower=description.lower(),
            model=model,
        )
    )
    (src_dir / "tools.py").write_text(_TOOLS_TEMPLATE.format(name=name))
    (tests_dir / "__init__.py").write_text(_TEST_INIT.format(package=package))

    return agent_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new agent in the workspace",
    )
    parser.add_argument("name", help="Agent name in kebab-case (e.g. finance-agent)")
    parser.add_argument(
        "--description",
        "-d",
        default="A helpful assistant",
        help="Short description of what the agent does",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gpt-4.1",
        help="Model deployment name (default: gpt-4.1)",
    )
    args = parser.parse_args()

    try:
        agent_dir = scaffold(args.name, args.description, args.model)
    except (FileNotFoundError, FileExistsError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    package = _to_snake(args.name)
    print(f"Agent '{args.name}' created at {agent_dir}")
    print()
    print("Next steps:")
    print(f"  1. Edit agents/{args.name}/src/{package}/tools.py — add your tools")
    print(f"  2. Edit agents/{args.name}/src/{package}/config.py — adjust instructions")
    print("  3. Run: uv sync")
    print("  4. Run: uv run python -m agent_core.validate")
    print("  5. The router will auto-discover your agent")


if __name__ == "__main__":
    main()
