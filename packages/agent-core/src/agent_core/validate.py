"""Validate all agent plugins in the workspace.

Checks that every agent in agents/ has the correct exports
and that all configured tools are callable.

Usage::

    uv run python -m agent_core.validate
"""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from types import ModuleType

from .config import AgentConfig
from .factory import MCP_PREFIX

logger = logging.getLogger(__name__)


def _find_agents_dir() -> Path:
    candidate = Path.cwd() / "agents"
    if candidate.is_dir():
        return candidate
    msg = "Could not find agents/ directory. Run from workspace root."
    raise FileNotFoundError(msg)


def _validate_agent(
    name: str,
    module: ModuleType,
) -> list[str]:
    """Validate a single agent module. Returns list of errors."""
    errors: list[str] = []

    # Check config export
    config = getattr(module, "config", None)
    if config is None:
        errors.append("missing `config` export in __init__.py")
        return errors

    if not isinstance(config, AgentConfig):
        errors.append(f"`config` is {type(config).__name__}, expected AgentConfig")
        return errors

    # Check tools export
    tools = getattr(module, "tools", None)
    if tools is None:
        errors.append("missing `tools` export in __init__.py")
        return errors

    if not isinstance(tools, ModuleType):
        errors.append(f"`tools` is {type(tools).__name__}, expected module")
        return errors

    # Check each tool is callable
    for tool_name in config.tools:
        if tool_name.startswith(MCP_PREFIX):
            continue  # MCP tools are resolved at runtime
        func = getattr(tools, tool_name, None)
        if func is None:
            errors.append(f"tool '{tool_name}' not found in tools module")
        elif not callable(func):
            errors.append(f"tool '{tool_name}' is not callable")

    return errors


def validate_all() -> dict[str, list[str]]:
    """Validate all agents. Returns {agent_dir_name: [errors]}."""
    agents_dir = _find_agents_dir()
    results: dict[str, list[str]] = {}
    seen_names: dict[str, str] = {}

    for child in sorted(agents_dir.iterdir()):
        if not child.is_dir() or child.name == "router":
            continue

        package_name = child.name.replace("-", "_")

        try:
            module = importlib.import_module(package_name)
        except ImportError:
            results[child.name] = [f"cannot import '{package_name}' (run `uv sync`)"]
            continue

        errors = _validate_agent(child.name, module)

        # Check for duplicate agent names
        config = getattr(module, "config", None)
        if isinstance(config, AgentConfig):
            if config.name in seen_names:
                errors.append(
                    f"duplicate name '{config.name}' "
                    f"(also in {seen_names[config.name]})"
                )
            else:
                seen_names[config.name] = child.name

        results[child.name] = errors

    return results


def main() -> None:
    logging.basicConfig(level=logging.WARNING)

    try:
        results = validate_all()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No agents found in agents/ directory.")
        sys.exit(0)

    has_errors = False

    for name, errors in results.items():
        # Get agent info for display
        package = name.replace("-", "_")
        try:
            module = importlib.import_module(package)
            config = getattr(module, "config", None)
        except ImportError:
            config = None

        if errors:
            has_errors = True
            print(f"  {name}: {errors[0]}  [FAIL]")
            for err in errors[1:]:
                print(f"    - {err}")
        elif isinstance(config, AgentConfig):
            tool_count = len(config.tools)
            fs = "file_search=on" if config.file_search_enabled else ""
            parts = [f"{tool_count} tools"]
            if fs:
                parts.append(fs)
            print(f"  {name}: {', '.join(parts)}  [OK]")
        else:
            print(f"  {name}:  [OK]")

    if has_errors:
        print("\nValidation failed.")
        sys.exit(1)
    else:
        print(f"\nAll {len(results)} agents valid.")


if __name__ == "__main__":
    main()
