"""Tests for agent-core registry and demo agent tools."""

from __future__ import annotations

from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent_core import AgentConfig, AgentRegistry


def _config(
    name: str,
    description: str = "",
) -> AgentConfig:
    return AgentConfig(
        name=name,
        instructions=f"You are {name}.",
        description=description,
    )


def _tools_module() -> ModuleType:
    return ModuleType("fake_tools")


class TestAgentRegistry:
    def test_register_and_get(self) -> None:
        reg = AgentRegistry()
        cfg = _config("a", "Agent A")
        reg.register(cfg, _tools_module())
        assert reg.get("a").config is cfg

    def test_duplicate_raises(self) -> None:
        reg = AgentRegistry()
        reg.register(_config("a"), _tools_module())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(_config("a"), _tools_module())

    def test_get_missing_raises(self) -> None:
        reg = AgentRegistry()
        with pytest.raises(KeyError):
            reg.get("missing")

    def test_list_agents(self) -> None:
        reg = AgentRegistry()
        reg.register(_config("x"), _tools_module())
        reg.register(_config("y"), _tools_module())
        names = [a.config.name for a in reg.list_agents()]
        assert names == ["x", "y"]

    def test_describe_agents(self) -> None:
        reg = AgentRegistry()
        reg.register(_config("x", "Does X"), _tools_module())
        desc = reg.describe_agents()
        assert "x" in desc and "Does X" in desc

    def test_len_and_contains(self) -> None:
        reg = AgentRegistry()
        reg.register(_config("a"), _tools_module())
        assert len(reg) == 1
        assert "a" in reg


class TestHelpdeskTools:
    def test_search_kb_vpn(self) -> None:
        from helpdesk.tools import search_knowledge_base

        result = search_knowledge_base("vpn connection fails")
        assert "vpn" in result.lower()

    def test_search_kb_no_results(self) -> None:
        from helpdesk.tools import search_knowledge_base

        result = search_knowledge_base("quantum entanglement")
        assert "no matching" in result.lower()

    def test_list_tickets(self) -> None:
        from helpdesk.tools import list_tickets

        result = list_tickets("all")
        # Either shows tickets (TKT-...) or says none found
        assert "tkt-" in result.lower() or "no tickets" in result.lower()

    def test_create_ticket(self) -> None:
        from helpdesk.tools import create_ticket

        result = create_ticket(
            "Monitor broken",
            "External monitor not detected",
            "high",
        )
        assert "TKT-" in result

    def test_create_ticket_invalid_priority(self) -> None:
        from helpdesk.tools import create_ticket

        result = create_ticket("Test", "Desc", "urgent")
        assert "invalid" in result.lower()


class TestKnowledgeTools:
    def test_search_remote_work(self) -> None:
        from knowledge_agent.tools import search_documents

        result = search_documents("remote work")
        assert "remote" in result.lower()

    def test_search_leave_policy(self) -> None:
        from knowledge_agent.tools import search_documents

        result = search_documents("leave days")
        assert "leave" in result.lower()

    def test_search_no_results(self) -> None:
        from knowledge_agent.tools import search_documents

        result = search_documents("xyznonexistent")
        assert "no matching" in result.lower()

    def test_list_documents(self) -> None:
        from knowledge_agent.tools import list_available_documents

        result = list_available_documents()
        assert "handbook" in result.lower()
        assert "it" in result.lower()


class TestDataAnalystTools:
    def test_describe_tables(self) -> None:
        from data_analyst.tools import describe_tables

        result = describe_tables()
        assert "employees" in result
        assert "projects" in result
        assert "tickets" in result

    def test_run_sql_select(self) -> None:
        from data_analyst.tools import run_sql

        result = run_sql(
            "SELECT COUNT(*) as n FROM employees",
        )
        assert "20" in result

    def test_run_sql_rejects_non_select(self) -> None:
        from data_analyst.tools import run_sql

        result = run_sql("DROP TABLE employees")
        assert "only select" in result.lower()

    def test_run_sql_handles_error(self) -> None:
        from data_analyst.tools import run_sql

        result = run_sql("SELECT * FROM nonexistent")
        assert "sql error" in result.lower()

    def test_get_sample_rows(self) -> None:
        from data_analyst.tools import get_sample_rows

        result = get_sample_rows("employees", 3)
        assert "name" in result.lower()

    def test_query_department_count(self) -> None:
        from data_analyst.tools import run_sql

        result = run_sql(
            "SELECT department, COUNT(*) as count "
            "FROM employees GROUP BY department "
            "ORDER BY count DESC",
        )
        assert "engineering" in result.lower()


def _mock_a2a_agent() -> MagicMock:
    """Create a mock A2AAgent that supports async context manager protocol."""
    mock = MagicMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)
    return mock


class TestRemoteAgents:
    @pytest.mark.asyncio
    async def test_register_remote_and_describe(self) -> None:
        mock_a2a = _mock_a2a_agent()
        mock_a2a.name = "remote-legal"
        mock_a2a.description = "Legal advice"

        reg = AgentRegistry()
        with patch(
            "agent_core.registry.A2AAgent",
            return_value=mock_a2a,
        ):
            await reg.register_remote(
                name="remote-legal",
                url="https://legal.internal/a2a",
            )

        assert "remote-legal" in reg
        desc = reg.describe_agents()
        assert "remote-legal" in desc

    @pytest.mark.asyncio
    async def test_register_remote_duplicate_raises(self) -> None:
        mock_a2a = _mock_a2a_agent()

        reg = AgentRegistry()
        with patch(
            "agent_core.registry.A2AAgent",
            return_value=mock_a2a,
        ):
            await reg.register_remote(name="dup", url="http://x")
            with pytest.raises(
                ValueError,
                match="already registered",
            ):
                await reg.register_remote(name="dup", url="http://x")

    @pytest.mark.asyncio
    async def test_close_cleans_up(self) -> None:
        mock_a2a = _mock_a2a_agent()

        reg = AgentRegistry()
        with patch(
            "agent_core.registry.A2AAgent",
            return_value=mock_a2a,
        ):
            await reg.register_remote(name="temp", url="http://x")

        assert "temp" in reg
        await reg.close()
        assert "temp" not in reg


class TestAgentConfig:
    def test_default_model(self) -> None:
        assert _config("test").model == "gpt-4.1"

    def test_custom_model(self) -> None:
        cfg = AgentConfig(
            name="test",
            instructions="test",
            model="gpt-4.1-mini",
        )
        assert cfg.model == "gpt-4.1-mini"

    def test_no_tool_approval_mode(self) -> None:
        assert not hasattr(
            _config("test"),
            "tool_approval_mode",
        )
