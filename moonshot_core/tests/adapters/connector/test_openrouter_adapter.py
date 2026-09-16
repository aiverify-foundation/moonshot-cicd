"""
Tests for the OpenRouterAdapter class.

This module contains tests for the OpenRouterAdapter class, which handles
communication with OpenRouter's OpenAI-compatible API for chat completions.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, ANY
from openai import BadRequestError

from adapters.connector.openrouter_adapter import (
    DEFAULT_OPENROUTER_BASE_URL,
    OpenRouterAdapter,
)
from domain.entities.connector_entity import ConnectorEntity


@pytest.fixture(autouse=True)
def _default_no_db_api_key_for_openrouter_configure(request):
    """
    OpenRouterAdapter.configure always queries DB by provider system_name; tests that only mock
    getenv expect no stored key — default the lookup to None unless the test patches this service.
    """
    if request.node.get_closest_marker("use_real_openrouter_db_key_lookup"):
        yield
        return
    with patch(
        "adapters.connector.openrouter_adapter.ProviderConnectorEnvKeyService"
    ) as mock_class:
        mock_inst = MagicMock()
        mock_inst.get_plain_api_key_for_provider_system_name.return_value = None
        mock_class.return_value = mock_inst
        yield


@pytest.fixture
def connector_entity():
    """Create a test connector entity for OpenRouter."""
    return ConnectorEntity(
        connector_adapter="openrouter_adapter",
        model="google/gemma-4-31b-it:free",
        model_endpoint="https://openrouter.ai/api/v1",
        params={
            "temperature": 0.7,
            "max_tokens": 1000,
        },
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt="You are a helpful assistant.",
    )


@pytest.fixture
def openrouter_adapter():
    """Create an OpenRouter adapter instance."""
    return OpenRouterAdapter()


# ================================
# Test configure
# ================================
def test_configure_with_api_key_and_endpoint(openrouter_adapter, connector_entity):
    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        openrouter_adapter.configure(connector_entity)

        assert openrouter_adapter.connector_entity == connector_entity
        assert openrouter_adapter._client == mock_client
        mock_openai_class.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://openrouter.ai/api/v1",
        )


def test_configure_prefers_db_api_key_from_provider_system_name(
    openrouter_adapter, connector_entity
):
    """Stored provider key wins over OPENROUTER_API_KEY."""
    with (
        patch(
            "adapters.connector.openrouter_adapter.ProviderConnectorEnvKeyService"
        ) as mock_svc_class,
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "env-key"
        mock_svc = MagicMock()
        mock_svc.get_plain_api_key_for_provider_system_name.return_value = "db-key"
        mock_svc_class.return_value = mock_svc
        mock_openai_class.return_value = MagicMock()

        openrouter_adapter.configure(connector_entity)

        mock_svc.get_plain_api_key_for_provider_system_name.assert_called_once_with(
            provider_system_name=OpenRouterAdapter.SYSTEM_NAME,
            version=OpenRouterAdapter.VERSION,
        )
        mock_openai_class.assert_called_once_with(
            api_key="db-key",
            base_url="https://openrouter.ai/api/v1",
        )


def test_configure_falls_back_to_env_when_db_key_missing(
    openrouter_adapter, connector_entity
):
    with (
        patch(
            "adapters.connector.openrouter_adapter.ProviderConnectorEnvKeyService"
        ) as mock_svc_class,
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "env-key"
        mock_svc = MagicMock()
        mock_svc.get_plain_api_key_for_provider_system_name.return_value = None
        mock_svc_class.return_value = mock_svc
        mock_openai_class.return_value = MagicMock()

        openrouter_adapter.configure(connector_entity)

        mock_getenv.assert_called_with("OPENROUTER_API_KEY")
        mock_openai_class.assert_called_once_with(
            api_key="env-key",
            base_url="https://openrouter.ai/api/v1",
        )


def test_configure_prefers_params_api_key_over_db_and_env(
    openrouter_adapter, connector_entity
):
    connector_entity.params = {**connector_entity.params, "api_key": "params-key"}
    with (
        patch(
            "adapters.connector.openrouter_adapter.ProviderConnectorEnvKeyService"
        ) as mock_svc_class,
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "env-key"
        mock_svc = MagicMock()
        mock_svc.get_plain_api_key_for_provider_system_name.return_value = "db-key"
        mock_svc_class.return_value = mock_svc
        mock_openai_class.return_value = MagicMock()

        openrouter_adapter.configure(connector_entity)

        mock_svc.get_plain_api_key_for_provider_system_name.assert_not_called()
        mock_openai_class.assert_called_once_with(
            api_key="params-key",
            base_url="https://openrouter.ai/api/v1",
        )


def test_configure_raises_type_error_when_system_name_empty(
    openrouter_adapter, connector_entity
):
    class BrokenOpenRouter(OpenRouterAdapter):
        SYSTEM_NAME = ""

    with pytest.raises(TypeError, match="SYSTEM_NAME"):
        BrokenOpenRouter().configure(connector_entity)


def test_configure_with_empty_api_key(openrouter_adapter, connector_entity):
    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = None
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        openrouter_adapter.configure(connector_entity)

        mock_openai_class.assert_called_once_with(
            api_key=ANY,
            base_url="https://openrouter.ai/api/v1",
        )


def test_configure_defaults_base_url_when_no_endpoint(
    openrouter_adapter, connector_entity
):
    """Empty model_endpoint uses OpenRouter's default API base URL."""
    connector_entity.model_endpoint = ""

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        openrouter_adapter.configure(connector_entity)

        mock_openai_class.assert_called_once_with(
            api_key="test-api-key",
            base_url=DEFAULT_OPENROUTER_BASE_URL,
        )


# ================================
# Test _process_response
# ================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "simple_response",
            "response_content": "This is a test response",
            "expected_result": "This is a test response",
        },
        {
            "name": "empty_response",
            "response_content": "",
            "expected_result": "",
        },
        {
            "name": "none_content",
            "response_content": None,
            "expected_result": None,
        },
    ],
)
async def test_process_response_success_cases(openrouter_adapter, test_case):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = test_case["response_content"]

    result = await openrouter_adapter._process_response(mock_response)
    assert result == test_case["expected_result"]


@pytest.mark.asyncio
async def test_process_response_missing_choices(openrouter_adapter):
    mock_response = MagicMock()
    mock_response.choices = []

    with pytest.raises(IndexError):
        await openrouter_adapter._process_response(mock_response)


# ================================
# Test get_response
# ================================
@pytest.mark.asyncio
async def test_get_response_success_with_system_prompt(
    openrouter_adapter, connector_entity
):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Test response"

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        openrouter_adapter.configure(connector_entity)
        result = await openrouter_adapter.get_response("Test prompt")

        assert result.response == "Test response"
        call_args = mock_client.chat.completions.create.call_args.kwargs
        expected_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test prompt"},
        ]
        assert call_args["messages"] == expected_messages


@pytest.mark.asyncio
async def test_get_response_success_without_system_prompt(
    openrouter_adapter, connector_entity
):
    connector_entity.system_prompt = ""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Test response"

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        openrouter_adapter.configure(connector_entity)
        await openrouter_adapter.get_response("Test prompt")

        call_args = mock_client.chat.completions.create.call_args.kwargs
        assert call_args["messages"] == [{"role": "user", "content": "Test prompt"}]


@pytest.mark.asyncio
async def test_get_response_with_pre_post_prompts(openrouter_adapter, connector_entity):
    connector_entity.connector_pre_prompt = "Pre: "
    connector_entity.connector_post_prompt = " :Post"
    connector_entity.system_prompt = ""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Test response"

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        openrouter_adapter.configure(connector_entity)
        await openrouter_adapter.get_response("Test")

        call_args = mock_client.chat.completions.create.call_args.kwargs
        assert call_args["messages"] == [
            {"role": "user", "content": "Pre: Test :Post"}
        ]


@pytest.mark.asyncio
async def test_get_response_api_exception(openrouter_adapter, connector_entity):
    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openrouter_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("OpenRouter API error")
        )

        openrouter_adapter.configure(connector_entity)

        with pytest.raises(Exception) as exc_info:
            await openrouter_adapter.get_response("Test prompt")

        assert str(exc_info.value) == "OpenRouter API error"
        mock_logger.error.assert_called_once()
        assert (
            OpenRouterAdapter.ERROR_PROCESSING_PROMPT
            in mock_logger.error.call_args.args[0]
        )


@pytest.mark.asyncio
async def test_get_response_strips_api_type_from_create_kwargs(
    openrouter_adapter, connector_entity
):
    connector_entity.params = {"api_type": "openai", "temperature": 0.2}
    connector_entity.system_prompt = ""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "ok"

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        openrouter_adapter.configure(connector_entity)
        await openrouter_adapter.get_response("Hi")

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "api_type" not in kwargs
        assert kwargs.get("temperature") == 0.2


@pytest.mark.asyncio
async def test_get_response_coerces_string_temperature_to_float(
    openrouter_adapter, connector_entity
):
    connector_entity.params = {
        "api_type": "openai",
        "temperature": "0.2",
        "max_tokens": "100",
    }
    connector_entity.system_prompt = ""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "ok"

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        openrouter_adapter.configure(connector_entity)
        await openrouter_adapter.get_response("Hi")

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs.get("temperature") == 0.2
        assert isinstance(kwargs.get("temperature"), float)
        assert kwargs.get("max_tokens") == 100
        assert isinstance(kwargs.get("max_tokens"), int)


@pytest.mark.asyncio
async def test_get_response_additional_params(openrouter_adapter, connector_entity):
    connector_entity.params = {
        "temperature": 0.9,
        "max_tokens": 2000,
        "top_p": 0.8,
    }
    connector_entity.system_prompt = ""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Response with params"

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        openrouter_adapter.configure(connector_entity)
        await openrouter_adapter.get_response("Test")

        call_args = mock_client.chat.completions.create.call_args.kwargs
        assert call_args["temperature"] == 0.9
        assert call_args["max_tokens"] == 2000
        assert call_args["top_p"] == 0.8
        assert call_args["model"] == "google/gemma-4-31b-it:free"


@pytest.mark.asyncio
async def test_get_response_logs_on_unexpected_keyword_typeerror(
    openrouter_adapter, connector_entity
):
    connector_entity.params = {"temperature": 0.1}
    connector_entity.system_prompt = ""

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openrouter_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            side_effect=TypeError("got an unexpected keyword argument 'bad_key'")
        )

        openrouter_adapter.configure(connector_entity)
        with pytest.raises(TypeError):
            await openrouter_adapter.get_response("Hi")

        mock_logger.error.assert_called_once()
        logged = mock_logger.error.call_args.args[0]
        assert OpenRouterAdapter.LOG_UNSUPPORTED_CHAT_KWARG in logged
        assert "unexpected keyword argument" in logged.lower()
        assert "connector_param_keys=" in logged


@pytest.mark.asyncio
async def test_get_response_logs_on_bad_request_error(
    openrouter_adapter, connector_entity
):
    connector_entity.system_prompt = ""
    mock_response = MagicMock()
    mock_response.status_code = 400
    err = BadRequestError(
        "invalid parameter",
        response=mock_response,
        body={"error": {"message": "invalid"}},
    )

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openrouter_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=err)

        openrouter_adapter.configure(connector_entity)
        with pytest.raises(BadRequestError):
            await openrouter_adapter.get_response("Hi")

        mock_logger.error.assert_called_once()
        logged = mock_logger.error.call_args.args[0]
        assert OpenRouterAdapter.LOG_API_REJECTED_CHAT in logged
        assert "invalid parameter" in logged


@pytest.mark.asyncio
async def test_get_response_logs_generic_on_runtime_error(
    openrouter_adapter, connector_entity
):
    connector_entity.system_prompt = ""

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openrouter_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("network")
        )

        openrouter_adapter.configure(connector_entity)
        with pytest.raises(RuntimeError, match="network"):
            await openrouter_adapter.get_response("Hi")

        mock_logger.error.assert_called_once()
        assert (
            OpenRouterAdapter.ERROR_PROCESSING_PROMPT
            in mock_logger.error.call_args.args[0]
        )


@pytest.mark.asyncio
async def test_get_response_typeerror_without_unexpected_keyword_uses_generic_log(
    openrouter_adapter, connector_entity
):
    connector_entity.system_prompt = ""

    with (
        patch("adapters.connector.openrouter_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openrouter_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openrouter_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            side_effect=TypeError("unsupported operand type(s)")
        )

        openrouter_adapter.configure(connector_entity)
        with pytest.raises(TypeError, match="unsupported operand"):
            await openrouter_adapter.get_response("Hi")

        mock_logger.error.assert_called_once()
        logged = mock_logger.error.call_args.args[0]
        assert OpenRouterAdapter.ERROR_PROCESSING_PROMPT in logged
        assert OpenRouterAdapter.LOG_UNSUPPORTED_CHAT_KWARG not in logged
