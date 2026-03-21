"""Tests for middleware — input guard, logging, and early termination."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from agent_core.middleware import (
    InputGuardMiddleware,
    LoggingAgentMiddleware,
    LoggingFunctionMiddleware,
)
from agent_framework import Message, MiddlewareTermination


class TestInputGuard:
    @pytest.mark.asyncio
    async def test_blocks_long_input(self) -> None:
        guard = InputGuardMiddleware(max_input_length=10, max_turns=50)
        ctx = MagicMock()
        ctx.messages = [MagicMock(text="x" * 100, role="user")]
        call_next = AsyncMock()

        with pytest.raises(MiddlewareTermination):
            await guard.process(ctx, call_next)

        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_allows_short_input(self) -> None:
        guard = InputGuardMiddleware(max_input_length=100, max_turns=50)
        ctx = MagicMock()
        ctx.messages = [MagicMock(text="hello", role="user")]
        call_next = AsyncMock()

        await guard.process(ctx, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_allows_empty_messages(self) -> None:
        guard = InputGuardMiddleware(max_input_length=100, max_turns=50)
        ctx = MagicMock()
        ctx.messages = []
        call_next = AsyncMock()

        await guard.process(ctx, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_blocks_excessive_turns(self) -> None:
        guard = InputGuardMiddleware(max_input_length=4000, max_turns=2)
        ctx = MagicMock()
        ctx.messages = [Message("user", ["q"]) for _ in range(5)]
        call_next = AsyncMock()

        with pytest.raises(MiddlewareTermination):
            await guard.process(ctx, call_next)


class TestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_agent_middleware_calls_next(self) -> None:
        middleware = LoggingAgentMiddleware()
        ctx = MagicMock()
        ctx.messages = [MagicMock(text="test input")]
        ctx.result = None
        call_next = AsyncMock()

        await middleware.process(ctx, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_function_middleware_calls_next(self) -> None:
        middleware = LoggingFunctionMiddleware()
        ctx = MagicMock()
        ctx.function = MagicMock()
        ctx.function.name = "test_tool"
        ctx.arguments = {"q": "test"}
        ctx.result = "result"
        call_next = AsyncMock()

        await middleware.process(ctx, call_next)
        call_next.assert_called_once()
