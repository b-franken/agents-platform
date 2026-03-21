"""Agent factory — creates agents from config + tools module."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.observability import configure_otel_providers
from azure.identity import AzureCliCredential, ManagedIdentityCredential
from dotenv import load_dotenv

from .middleware import (
    InputGuardMiddleware,
    LoggingAgentMiddleware,
    LoggingFunctionMiddleware,
)

if TYPE_CHECKING:
    from types import ModuleType

    from agent_framework import Agent

    from .config import AgentConfig

__all__ = ["create_agent_from_config", "create_client"]

MCP_PREFIX: str = "mcp:"

logger = logging.getLogger(__name__)

_observability_initialized: bool = False


def _init_observability() -> None:
    global _observability_initialized
    if _observability_initialized:
        return
    if os.getenv("ENABLE_INSTRUMENTATION", "false").lower() == "true":
        configure_otel_providers()
        logger.info("OpenTelemetry observability activated")
    _observability_initialized = True


def _get_credential() -> ManagedIdentityCredential | AzureCliCredential | None:
    """Explicit credential selection — no fallback chains.

    - AZURE_OPENAI_API_KEY set → API key auth (no credential object needed)
    - AZURE_CLIENT_ID set → ManagedIdentityCredential (production)
    - Neither → AzureCliCredential (development, requires ``az login``)
    """
    if os.getenv("AZURE_OPENAI_API_KEY"):
        logger.debug("Auth: API key")
        return None
    if os.getenv("AZURE_CLIENT_ID"):
        logger.debug("Auth: ManagedIdentityCredential")
        return ManagedIdentityCredential()
    logger.debug("Auth: AzureCliCredential (development)")
    return AzureCliCredential()


def create_client(model: str | None = None) -> AzureOpenAIResponsesClient:
    """Create an AzureOpenAIResponsesClient.

    Args:
        model: Deployment name override.
            Falls back to AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME.
    """
    load_dotenv()
    _init_observability()

    deployment_name = (
        model
        or os.getenv("AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")
        or "gpt-4.1"
    )
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    credential = _get_credential()

    if api_key:
        return AzureOpenAIResponsesClient(
            deployment_name=deployment_name,
            api_key=api_key,
        )

    if endpoint and credential:
        if "/api/projects/" in endpoint:
            return AzureOpenAIResponsesClient(
                deployment_name=deployment_name,
                credential=credential,
                project_endpoint=endpoint,
            )
        return AzureOpenAIResponsesClient(
            deployment_name=deployment_name,
            credential=credential,
            endpoint=endpoint,
        )

    if credential:
        return AzureOpenAIResponsesClient(
            deployment_name=deployment_name,
            credential=credential,
        )

    return AzureOpenAIResponsesClient(deployment_name=deployment_name)


def _parse_mcp_tool_spec(spec: str) -> tuple[str, str]:
    """Parse 'mcp:<name>:<url>' into (name, url)."""
    parts = spec.removeprefix(MCP_PREFIX).split(":", 1)
    if len(parts) != 2:
        msg = f"Invalid MCP tool spec '{spec}'. Expected format: mcp:<name>:<url>"
        raise ValueError(msg)
    return parts[0], parts[1]


def _resolve_tools(
    config: AgentConfig,
    tools_module: ModuleType,
    client: AzureOpenAIResponsesClient,
) -> list[object]:
    """Resolve tool names to actual tool objects.

    Supports two formats:
    - Plain function name: looked up in tools_module (e.g. "get_team_info")
    - MCP tool: prefixed with "mcp:" (e.g. "mcp:confluence:http://localhost:3000/mcp")
    """
    resolved: list[object] = []

    for tool_name in config.tools:
        if tool_name.startswith(MCP_PREFIX):
            name, url = _parse_mcp_tool_spec(tool_name)
            resolved.append(client.get_mcp_tool(name=name, url=url))
            logger.info("MCP tool registered: %s → %s", name, url)
        else:
            func = getattr(tools_module, tool_name, None)
            if func is None:
                msg = f"Tool '{tool_name}' not found in {tools_module.__name__}"
                raise ValueError(msg)
            if not callable(func):
                msg = f"'{tool_name}' in {tools_module.__name__} is not callable"
                raise TypeError(msg)
            resolved.append(func)

    if config.file_search_enabled:
        vector_store_id = os.getenv("VECTOR_STORE_ID")
        if vector_store_id:
            resolved.append(
                client.get_file_search_tool(vector_store_ids=[vector_store_id])
            )
            logger.info("File search enabled (vector store: %s)", vector_store_id)

    return resolved


def create_agent_from_config(
    config: AgentConfig,
    tools_module: ModuleType,
    client: AzureOpenAIResponsesClient | None = None,
) -> tuple[Agent, AzureOpenAIResponsesClient]:
    """Create an agent from an AgentConfig and a tools module."""
    if client is None:
        client = create_client(model=config.model)

    agent_tools = _resolve_tools(config, tools_module, client)

    agent = client.as_agent(
        name=config.name,
        description=config.description,
        instructions=config.instructions,
        tools=agent_tools,
        middleware=[
            InputGuardMiddleware(
                max_input_length=config.max_input_length,
                max_turns=config.max_conversation_turns,
            ),
            LoggingAgentMiddleware(),
            LoggingFunctionMiddleware(),
        ],
    )

    logger.info("Agent '%s' created with %d tools", config.name, len(agent_tools))
    return agent, client
