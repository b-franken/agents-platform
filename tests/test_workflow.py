"""Tests for workflow building — HandoffBuilder orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent_core import AgentConfig, AgentRegistry


def _registry_with_agents(*names: str) -> AgentRegistry:
    reg = AgentRegistry()
    for name in names:
        cfg = AgentConfig(
            name=name,
            instructions=f"You are {name}.",
            description=f"Handles {name}",
        )
        reg.register(cfg, MagicMock())
    return reg


def _mock_handoff_builder() -> MagicMock:
    builder = MagicMock()
    builder.with_start_agent.return_value = builder
    builder.add_handoff.return_value = builder
    builder.with_autonomous_mode.return_value = builder
    builder.build.return_value = MagicMock()
    return builder


class TestWorkflowBuilding:
    @patch("agent_core.registry.HandoffBuilder")
    @patch("agent_core.factory.create_agent_from_config")
    def test_builds_with_all_agents(
        self, mock_create, mock_hb_cls,
    ) -> None:
        mock_create.return_value = (MagicMock(), MagicMock())
        mock_builder = _mock_handoff_builder()
        mock_hb_cls.return_value = mock_builder

        reg = _registry_with_agents("helpdesk", "data-analyst")
        triage = MagicMock()

        reg.build_handoff_workflow(client=MagicMock(), triage_agent=triage)

        mock_hb_cls.assert_called_once()
        mock_builder.with_start_agent.assert_called_once_with(triage)
        # triage→all specialists + each specialist→triage
        assert mock_builder.add_handoff.call_count == 3
        mock_builder.build.assert_called_once()

    @patch("agent_core.registry.HandoffBuilder")
    @patch("agent_core.factory.create_agent_from_config")
    def test_autonomous_mode_disabled(
        self, mock_create, mock_hb_cls,
    ) -> None:
        mock_create.return_value = (MagicMock(), MagicMock())
        mock_builder = _mock_handoff_builder()
        mock_hb_cls.return_value = mock_builder

        reg = _registry_with_agents("agent-a")
        reg.build_handoff_workflow(
            client=MagicMock(),
            triage_agent=MagicMock(),
            autonomous_triage=False,
        )

        mock_builder.with_autonomous_mode.assert_not_called()

    @patch("agent_core.registry.HandoffBuilder")
    @patch("agent_core.factory.create_agent_from_config")
    def test_checkpoint_storage_passed(
        self, mock_create, mock_hb_cls,
    ) -> None:
        mock_create.return_value = (MagicMock(), MagicMock())
        mock_builder = _mock_handoff_builder()
        mock_hb_cls.return_value = mock_builder

        storage = MagicMock()
        reg = _registry_with_agents("agent-a")
        reg.build_handoff_workflow(
            client=MagicMock(),
            triage_agent=MagicMock(),
            checkpoint_storage=storage,
        )

        call_kwargs = mock_hb_cls.call_args.kwargs
        assert call_kwargs["checkpoint_storage"] is storage
