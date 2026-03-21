"""Agent middleware — logging, observability and guardrails."""

from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING

from agent_framework import (
    AgentContext,
    AgentMiddleware,
    AgentResponse,
    FunctionInvocationContext,
    FunctionMiddleware,
    Message,
    MiddlewareTermination,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

__all__ = [
    "InputGuardMiddleware",
    "LoggingAgentMiddleware",
    "LoggingFunctionMiddleware",
]

logger = logging.getLogger(__name__)


def _sensitive_data_enabled() -> bool:
    return os.getenv("ENABLE_SENSITIVE_DATA", "false").lower() == "true"


class LoggingAgentMiddleware(AgentMiddleware):
    """Logs every agent run: input preview, duration, output preview."""

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        last = context.messages[-1] if context.messages else None
        preview = (last.text or "")[:200] if last else "(no input)"

        logger.info("Agent run started | input: %s", preview)
        start = time.monotonic()

        await call_next()

        duration = time.monotonic() - start
        output = (
            str(context.result)[:200]
            if isinstance(context.result, AgentResponse)
            else ""
        )
        logger.info("Agent run completed | %.2fs | output: %s", duration, output)


class LoggingFunctionMiddleware(FunctionMiddleware):
    """Logs every tool call. Arguments only logged when ENABLE_SENSITIVE_DATA=true."""

    async def process(
        self,
        context: FunctionInvocationContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        name = context.function.name

        if _sensitive_data_enabled():
            logger.info("Tool call: %s | args: %s", name, context.arguments)
        else:
            logger.info("Tool call: %s", name)

        start = time.monotonic()
        await call_next()
        duration = time.monotonic() - start

        if _sensitive_data_enabled():
            preview = str(context.result)[:200] if context.result else "(empty)"
            logger.info(
                "Tool %s completed | %.2fs | result: %s",
                name,
                duration,
                preview,
            )
        else:
            logger.info("Tool %s completed | %.2fs", name, duration)


class InputGuardMiddleware(AgentMiddleware):
    """Validates input length and enforces conversation turn limits."""

    def __init__(self, max_input_length: int = 4000, max_turns: int = 50) -> None:
        self._max_input_length = max_input_length
        self._max_turns = max_turns

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        last = context.messages[-1] if context.messages else None

        if last and last.text and len(last.text) > self._max_input_length:
            logger.warning(
                "Input rejected: %d chars (max %d)",
                len(last.text),
                self._max_input_length,
            )
            msg = (
                f"Message too long ({len(last.text)} chars, "
                f"max {self._max_input_length}). "
                "Please shorten your question."
            )
            context.result = AgentResponse(messages=[Message("assistant", [msg])])
            raise MiddlewareTermination(result=context.result)

        user_turns = sum(
            1 for m in context.messages if isinstance(m, Message) and m.role == "user"
        )
        if user_turns > self._max_turns:
            logger.warning("Max turns reached: %d", user_turns)
            context.result = AgentResponse(
                messages=[
                    Message(
                        "assistant",
                        [
                            f"Conversation reached the {self._max_turns}-turn limit. "
                            "Please start a new session.",
                        ],
                    )
                ]
            )
            raise MiddlewareTermination(result=context.result)

        await call_next()
