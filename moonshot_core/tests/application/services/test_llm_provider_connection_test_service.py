from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.dto.provider_dto import TestLlmProviderConnectionBody
from application.services.llm_provider_connection_test_service import (
    CONNECTION_TEST_PROMPT, LlmProviderConnectionTestService)
from domain.entities.connector_response_entity import ConnectorResponseEntity


def _make_adapter(*, default_pairs=None, get_response=None):
    class FakeAdapter:
        DEFAULT_CONFIG_PAIRS = default_pairs or {}

    adapter = FakeAdapter()
    adapter.configure = MagicMock()
    adapter.get_response = get_response or AsyncMock(
        return_value=ConnectorResponseEntity(response="OK")
    )
    return adapter


@pytest.mark.asyncio
async def test_test_connection_uses_form_api_key():
    env_key_service = MagicMock()
    mock_adapter = _make_adapter(default_pairs={"temperature": "1.0"})

    body = TestLlmProviderConnectionBody(
        llm_provider_id=1,
        model_name="gpt-4o-mini",
        savedConfigPairs={"temperature": "0.2"},
        api_key="sk-test",
    )

    service = LlmProviderConnectionTestService(env_key_service=env_key_service)
    with (
        patch.object(
            service, "_load_provider_system_name", return_value="openai_adapter"
        ),
        patch(
            "application.services.llm_provider_connection_test_service.ModuleLoader.load",
            return_value=(mock_adapter, None),
        ),
    ):
        result = await service.test_connection(body)

    assert result.success is True
    assert result.response_preview == "OK"
    assert result.error is None
    mock_adapter.configure.assert_called_once()
    configured_entity = mock_adapter.configure.call_args.args[0]
    assert configured_entity.model == "gpt-4o-mini"
    assert configured_entity.params["api_key"] == "sk-test"
    assert configured_entity.params["temperature"] == "0.2"
    mock_adapter.get_response.assert_awaited_once_with(CONNECTION_TEST_PROMPT)
    env_key_service.get_plain_api_key_for_provider.assert_not_called()


@pytest.mark.asyncio
async def test_test_connection_uses_stored_key_when_form_key_missing():
    env_key_service = MagicMock()
    env_key_service.get_plain_api_key_for_provider.return_value = "stored-key"
    mock_adapter = _make_adapter()

    body = TestLlmProviderConnectionBody(
        llm_provider_id=7,
        model_name="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    )

    service = LlmProviderConnectionTestService(env_key_service=env_key_service)
    with (
        patch.object(
            service, "_load_provider_system_name", return_value="together_adapter"
        ),
        patch(
            "application.services.llm_provider_connection_test_service.ModuleLoader.load",
            return_value=(mock_adapter, None),
        ),
    ):
        result = await service.test_connection(body)

    assert result.success is True
    assert result.response_preview == "OK"
    env_key_service.get_plain_api_key_for_provider.assert_called_once_with(7)
    configured_entity = mock_adapter.configure.call_args.args[0]
    assert configured_entity.params["api_key"] == "stored-key"


@pytest.mark.asyncio
async def test_test_connection_returns_failure_when_get_response_raises():
    env_key_service = MagicMock()
    mock_adapter = _make_adapter(
        get_response=AsyncMock(side_effect=RuntimeError("auth failed"))
    )

    body = TestLlmProviderConnectionBody(
        llm_provider_id=1,
        model_name="gpt-4o-mini",
        api_key="sk-bad",
    )

    service = LlmProviderConnectionTestService(env_key_service=env_key_service)
    with (
        patch.object(
            service, "_load_provider_system_name", return_value="openai_adapter"
        ),
        patch(
            "application.services.llm_provider_connection_test_service.ModuleLoader.load",
            return_value=(mock_adapter, None),
        ),
    ):
        result = await service.test_connection(body)

    assert result.success is False
    assert result.error == "auth failed"
    assert result.response_preview is None


def test_resolve_api_key_requires_key():
    env_key_service = MagicMock()
    env_key_service.get_plain_api_key_for_provider.return_value = None
    service = LlmProviderConnectionTestService(env_key_service=env_key_service)

    with pytest.raises(ValueError, match="API key is required"):
        service._resolve_api_key(
            TestLlmProviderConnectionBody(llm_provider_id=1, model_name="gpt-4o-mini")
        )


@pytest.mark.asyncio
async def test_test_connection_requires_model_name():
    service = LlmProviderConnectionTestService(env_key_service=MagicMock())

    with pytest.raises(ValueError, match="model name is required"):
        await service.test_connection(
            TestLlmProviderConnectionBody(
                llm_provider_id=1, model_name="  ", api_key="sk"
            )
        )


@pytest.mark.asyncio
async def test_test_connection_rejects_unmapped_provider():
    env_key_service = MagicMock()
    service = LlmProviderConnectionTestService(env_key_service=env_key_service)

    with (
        patch.object(
            service, "_load_provider_system_name", return_value="unknown_provider"
        ),
        pytest.raises(ValueError, match="No connector adapter mapping"),
    ):
        await service.test_connection(
            TestLlmProviderConnectionBody(
                llm_provider_id=1,
                model_name="gpt-4o-mini",
                api_key="sk-test",
            )
        )
