"""Router entry point — Handoff workflow with checkpointing.

Usage:
    uv run --package router-agent python -m router.main
    uv run --package router-agent python -m router.main --resume
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

from agent_core.factory import create_client
from agent_framework import FileCheckpointStorage, Workflow, WorkflowEvent
from agent_framework.exceptions import AgentFrameworkException
from agent_framework.orchestrations import HandoffAgentUserRequest
from dotenv import load_dotenv

from .config import TRIAGE_INSTRUCTIONS, build_registry, register_a2a_agents

logger = logging.getLogger(__name__)


async def run(*, resume: bool = False) -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # --- Registry (local + remote A2A agents) -----------------------
    registry = build_registry()
    await register_a2a_agents(registry)

    client = create_client()

    triage = client.as_agent(
        name="triage",
        instructions=TRIAGE_INSTRUCTIONS.format(
            agents=registry.describe_agents(),
        ),
        description="Routes questions to the right specialist",
    )

    # --- Checkpointing ----------------------------------------------
    checkpoint_path = os.getenv(
        "CHECKPOINT_STORAGE_PATH",
        "./checkpoints",
    )
    storage = FileCheckpointStorage(storage_path=checkpoint_path)

    workflow = registry.build_handoff_workflow(
        client=client,
        triage_agent=triage,
        checkpoint_storage=storage,
    )

    logger.info(
        "Platform started — %d agents, checkpoints → %s",
        len(registry),
        checkpoint_path,
    )
    print("=" * 60)
    print(f"Agent Platform ({len(registry)} agents)")
    print(registry.describe_agents())
    print(f"Checkpoints: {checkpoint_path}")
    print("Type 'exit' to stop")
    print("=" * 60)
    print()

    # --- Resume from checkpoint if requested ------------------------
    if resume:
        checkpoints = await storage.list_checkpoints(
            workflow_name="internal_platform",
        )
        if checkpoints:
            latest = sorted(
                checkpoints,
                key=lambda c: c.timestamp,
                reverse=True,
            )[0]
            logger.info(
                "Resuming from checkpoint %s",
                latest.checkpoint_id,
            )
            events = [
                e
                async for e in workflow.run(
                    stream=True,
                    checkpoint_id=latest.checkpoint_id,
                )
            ]
            _print_events(events)
        else:
            print("No checkpoints found — starting fresh.")

    # --- Interactive loop -------------------------------------------
    try:
        await _interactive_loop(workflow)
    finally:
        await registry.close()


async def _read_input(prompt: str) -> str:
    """Read user input without blocking the event loop."""
    return (await asyncio.to_thread(input, prompt)).strip()


async def _interactive_loop(workflow: Workflow) -> None:
    """Run the interactive chat loop."""
    user_input: str | None = await _read_input("You > ")
    if not user_input or user_input.lower() in {"exit", "quit"}:
        return

    while True:
        try:
            events = [e async for e in workflow.run(user_input, stream=True)]
        except AgentFrameworkException:
            logger.exception("Error during workflow run")
            print("Something went wrong. Try again or 'exit'.")
            user_input = await _read_input("\nYou > ")
            continue

        pending = _print_events(events)

        if not pending:
            break

        try:
            user_input = await _read_input("\nYou > ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            return

        responses = {
            req.request_id: HandoffAgentUserRequest.create_response(
                user_input,
            )
            for req in pending
        }
        try:
            events = [
                e
                async for e in workflow.run(
                    stream=True,
                    responses=responses,
                )
            ]
        except AgentFrameworkException:
            logger.exception("Error during workflow run")
            print("Something went wrong.")
            continue

        _print_events(events)


def _print_events(events: list[WorkflowEvent]) -> list[WorkflowEvent]:
    """Print events and return pending request_info events."""
    pending: list[WorkflowEvent] = []
    for event in events:
        if event.type == "request_info" and isinstance(
            event.data, HandoffAgentUserRequest
        ):
            pending.append(event)
            for msg in event.data.agent_response.messages[-3:]:
                print(f"{msg.author_name}: {msg.text}")
        elif event.type == "output":
            print()
    return pending


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Start the agent platform",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )
    args = parser.parse_args()
    asyncio.run(run(resume=args.resume))


if __name__ == "__main__":
    main()
