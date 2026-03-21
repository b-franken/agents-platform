"""Tests for agent factory — client creation and credential selection."""

from __future__ import annotations

from unittest.mock import patch

from agent_core.factory import _get_credential, create_client


class TestCredentialSelection:
    """Verify explicit credential paths — no DefaultAzureCredential fallback."""

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=True)
    def test_api_key_returns_none(self) -> None:
        assert _get_credential() is None

    @patch.dict("os.environ", {"AZURE_CLIENT_ID": "managed-id"}, clear=True)
    def test_managed_identity(self) -> None:
        cred = _get_credential()
        assert type(cred).__name__ == "ManagedIdentityCredential"

    @patch.dict("os.environ", {}, clear=True)
    def test_cli_credential_fallback(self) -> None:
        cred = _get_credential()
        assert type(cred).__name__ == "AzureCliCredential"


class TestCreateClient:
    """Verify client construction per auth path."""

    @patch("agent_core.factory.AzureOpenAIResponsesClient")
    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "key123"}, clear=True)
    def test_api_key_path(self, mock_client_cls) -> None:
        create_client()
        mock_client_cls.assert_called_once_with(
            deployment_name="gpt-4.1",
            api_key="key123",
        )

    @patch("agent_core.factory.AzureOpenAIResponsesClient")
    @patch.dict(
        "os.environ",
        {
            "AZURE_AI_PROJECT_ENDPOINT": "https://hub.services.ai.azure.com/api/projects/my-project"
        },
        clear=True,
    )
    def test_credential_with_project_endpoint(self, mock_client_cls) -> None:
        create_client()
        call_kwargs = mock_client_cls.call_args.kwargs
        assert call_kwargs["deployment_name"] == "gpt-4.1"
        assert (
            call_kwargs["project_endpoint"]
            == "https://hub.services.ai.azure.com/api/projects/my-project"
        )
        assert "credential" in call_kwargs

    @patch("agent_core.factory.AzureOpenAIResponsesClient")
    @patch.dict(
        "os.environ",
        {"AZURE_AI_PROJECT_ENDPOINT": "https://myresource.openai.azure.com/"},
        clear=True,
    )
    def test_credential_with_openai_endpoint(self, mock_client_cls) -> None:
        create_client()
        call_kwargs = mock_client_cls.call_args.kwargs
        assert call_kwargs["deployment_name"] == "gpt-4.1"
        assert call_kwargs["endpoint"] == "https://myresource.openai.azure.com/"
        assert "credential" in call_kwargs

    @patch("agent_core.factory.AzureOpenAIResponsesClient")
    @patch.dict(
        "os.environ",
        {"AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME": "gpt-4.1-mini"},
        clear=True,
    )
    def test_model_override(self, mock_client_cls) -> None:
        create_client(model="custom-model")
        call_kwargs = mock_client_cls.call_args.kwargs
        assert call_kwargs["deployment_name"] == "custom-model"

    @patch("agent_core.factory.AzureOpenAIResponsesClient")
    @patch.dict("os.environ", {}, clear=True)
    def test_default_model_fallback(self, mock_client_cls) -> None:
        create_client()
        call_kwargs = mock_client_cls.call_args.kwargs
        assert call_kwargs["deployment_name"] == "gpt-4.1"
