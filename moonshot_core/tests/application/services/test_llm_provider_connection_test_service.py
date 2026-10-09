from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adapters.connector.aws_bedrock_adapter import AWSBedrockAdapter
from application.dto.provider_dto import TestLlmProviderConnectionBody
from application.services.llm_provider_connection_test_service import (
    CONNECTION_TEST_PROMPT,
    LlmProviderConnectionTestService,
)
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.feature_flags import FeatureFlags


@pytest.fixture(autouse=True)
def reset_feature_flags():
    FeatureFlags.reset()
    yield
    FeatureFlags.reset()


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


@pytest.mark.asyncio
async def test_test_connection_bedrock_allows_missing_api_key_when_flag_on():
    env_key_service = MagicMock()
    env_key_service.get_plain_api_key_for_provider.return_value = None
    mock_adapter = _make_adapter(default_pairs={"temperature": "1.0"})
    flag_adapter = MagicMock()
    flag_adapter.load_flags.return_value = {
        FeatureFlagNames.AIVET_OCT2026_MOON792: True
    }

    body = TestLlmProviderConnectionBody(
        llm_provider_id=3,
        model_name="anthropic.claude-3-haiku-20240307-v1:0",
        savedConfigPairs={"temperature": "0.5"},
    )

    service = LlmProviderConnectionTestService(env_key_service=env_key_service)
    with (
        patch(
            "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
            return_value=flag_adapter,
        ),
        patch.object(
            service,
            "_load_provider_system_name",
            return_value=AWSBedrockAdapter.SYSTEM_NAME,
        ),
        patch(
            "application.services.llm_provider_connection_test_service.ModuleLoader.load",
            return_value=(mock_adapter, None),
        ),
    ):
        result = await service.test_connection(body)

    assert result.success is True
    assert result.response_preview == "OK"
    env_key_service.get_plain_api_key_for_provider.assert_called_once_with(3)
    configured_entity = mock_adapter.configure.call_args.args[0]
    assert "api_key" not in configured_entity.params
    assert configured_entity.params["temperature"] == "0.5"


@pytest.mark.asyncio
async def test_test_connection_bedrock_passes_token_as_api_key():
    env_key_service = MagicMock()
    mock_adapter = _make_adapter(
        default_pairs={"temperature": "1.0", "aws_access_key_id": ""}
    )
    flag_adapter = MagicMock()
    flag_adapter.load_flags.return_value = {
        FeatureFlagNames.AIVET_OCT2026_MOON792: True
    }

    body = TestLlmProviderConnectionBody(
        llm_provider_id=3,
        model_name="anthropic.claude-3-haiku-20240307-v1:0",
        savedConfigPairs={
            "temperature": "0.5",
            "aws_access_key_id": "AKIATEST",
        },
        api_key="secret-from-token-field",
    )

    service = LlmProviderConnectionTestService(env_key_service=env_key_service)
    with (
        patch(
            "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
            return_value=flag_adapter,
        ),
        patch.object(
            service,
            "_load_provider_system_name",
            return_value=AWSBedrockAdapter.SYSTEM_NAME,
        ),
        patch(
            "application.services.llm_provider_connection_test_service.ModuleLoader.load",
            return_value=(mock_adapter, None),
        ),
    ):
        result = await service.test_connection(body)

    assert result.success is True
    env_key_service.get_plain_api_key_for_provider.assert_not_called()
    configured_entity = mock_adapter.configure.call_args.args[0]
    assert configured_entity.params["api_key"] == "secret-from-token-field"
    assert configured_entity.params["aws_access_key_id"] == "AKIATEST"


@pytest.mark.asyncio
async def test_test_connection_bedrock_rejected_when_flag_off():
    env_key_service = MagicMock()
    flag_adapter = MagicMock()
    flag_adapter.load_flags.return_value = {
        FeatureFlagNames.AIVET_OCT2026_MOON792: False
    }

    service = LlmProviderConnectionTestService(env_key_service=env_key_service)
    with (
        patch(
            "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
            return_value=flag_adapter,
        ),
        patch.object(
            service,
            "_load_provider_system_name",
            return_value=AWSBedrockAdapter.SYSTEM_NAME,
        ),
        pytest.raises(ValueError, match="unavailable"),
    ):
        await service.test_connection(
            TestLlmProviderConnectionBody(
                llm_provider_id=3,
                model_name="anthropic.claude-3-haiku-20240307-v1:0",
            )
        )
