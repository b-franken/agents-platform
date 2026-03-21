"""Tests for the scaffold CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from agent_core.scaffold import _to_snake, scaffold

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def tmp_agents_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary workspace with an agents/ directory."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    return agents_dir


class TestScaffold:
    def test_creates_directory_structure(self, tmp_agents_dir: Path) -> None:
        agent_dir = scaffold("test-agent", "A test agent", "gpt-4.1")

        assert agent_dir.exists()
        assert (agent_dir / "pyproject.toml").exists()
        assert (agent_dir / "src" / "test_agent" / "__init__.py").exists()
        assert (agent_dir / "src" / "test_agent" / "config.py").exists()
        assert (agent_dir / "src" / "test_agent" / "tools.py").exists()
        assert (agent_dir / "knowledge").is_dir()
        assert (agent_dir / "tests" / "__init__.py").exists()

    def test_pyproject_contains_agent_core_dep(self, tmp_agents_dir: Path) -> None:
        scaffold("my-agent", "My agent", "gpt-4.1")
        content = (tmp_agents_dir / "my-agent" / "pyproject.toml").read_text()

        assert 'name = "my-agent"' in content
        assert '"agent-core"' in content
        assert "workspace = true" in content

    def test_config_uses_provided_values(
        self,
        tmp_agents_dir: Path,
    ) -> None:
        scaffold("finance-agent", "Finance questions", "gpt-4.1-mini")
        cfg_path = (
            tmp_agents_dir / "finance-agent" / "src" / "finance_agent" / "config.py"
        )
        content = cfg_path.read_text()

        assert 'name="finance-agent"' in content
        assert "Finance questions" in content
        assert 'model="gpt-4.1-mini"' in content

    def test_tools_has_example(self, tmp_agents_dir: Path) -> None:
        scaffold("test-agent", "Test", "gpt-4.1")
        tools_path = tmp_agents_dir / "test-agent" / "src" / "test_agent" / "tools.py"
        content = tools_path.read_text()

        assert "@tool" in content
        assert "example_tool" in content

    def test_duplicate_raises(self, tmp_agents_dir: Path) -> None:
        scaffold("test-agent", "Test", "gpt-4.1")
        with pytest.raises(FileExistsError, match="already exists"):
            scaffold("test-agent", "Test", "gpt-4.1")

    def test_missing_agents_dir_raises(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError, match="agents/"):
            scaffold("test-agent", "Test", "gpt-4.1")


class TestToSnake:
    def test_kebab_to_snake(self) -> None:
        assert _to_snake("my-cool-agent") == "my_cool_agent"

    def test_no_hyphens(self) -> None:
        assert _to_snake("simple") == "simple"
