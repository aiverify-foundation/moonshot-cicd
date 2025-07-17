import re
import anthropic
import pytest
import adapters

from unittest.mock import AsyncMock, MagicMock, patch
from anthropic import AsyncAnthropic

from adapters.connector.anthropic_adapter import AnthropicAdapter
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity


# ================================
# Fixtures
# ================================
@pytest.fixture
def connector_entity() -> ConnectorEntity:
    """
    Create a test connector entity for Anthropic.

    Returns:
        ConnectorEntity: A test connector entity with complete Anthropic configuration.
    """
    return ConnectorEntity(
        connector_adapter="anthropic_adapter",
        model="claude-sonnet-4-20250514",
        model_endpoint="",
        params={
            "max_tokens": 1024
        },
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt=""
    )


@pytest.fixture
def anthropic_adapter() -> AnthropicAdapter:
    """
    Create an Anthropic adapter instance.

    Returns:
        AnthropicAdapter: A fresh Anthropic adapter instance for testing.
    """
    return AnthropicAdapter()


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """
    Create a mock AsyncAnthropic client.

    Returns:
        AsyncMock: A mock instance of AsyncAnthropic client.
    """
    mock_anthropic_client_response = MagicMock()
    mock_anthropic_client_response.content = [MagicMock]
    mock_anthropic_client_response.content[0].text = "Test response from Anthropic client."

    mock_anthropic_client = MagicMock()
    mock_anthropic_client.messages.create = AsyncMock(return_value=mock_anthropic_client_response)

    return mock_anthropic_client


# ================================
# Test configuration of Anthropic Adapter
# ================================
def test_configure_with_api_key_and_endpoint(anthropic_adapter: AnthropicAdapter,
                                             connector_entity: ConnectorEntity):
    """
    Test successful configuration with API key and custom endpoint.
    API Key is retrieved from environment variable ANTHROPIC_API_KEY.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv:
        mock_getenv.return_value = "test-api-key"
        connector_entity.model_endpoint = "https://api.testendpoint.com"

        anthropic_adapter.configure(connector_entity)

        assert anthropic_adapter.connector_entity == connector_entity
        assert isinstance(anthropic_adapter._client, AsyncAnthropic)
        assert anthropic_adapter._client.api_key == "test-api-key"
        assert anthropic_adapter._client.base_url == "https://api.testendpoint.com"


def test_configure_with_empty_api_key(anthropic_adapter: AnthropicAdapter,
                                      connector_entity: ConnectorEntity):
    """
    Test configuration with empty API key and empty model endpoint. If no API key is defined in
    environment variable "ANTHROPIC_API_KEY", it should default to empty string. If not endpoint is
    provided to Anthropic client, it would default to https://api.anthropic.com.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv:
        mock_getenv.return_value = None

        anthropic_adapter.configure(connector_entity)

        assert isinstance(anthropic_adapter._client, AsyncAnthropic)
        assert anthropic_adapter._client.api_key == ""


def test_configure_with_no_endpoint(anthropic_adapter: AnthropicAdapter,
                                    connector_entity: ConnectorEntity):
    """
    Test configuration with empty model endpoint.
    If not endpoint is provided to Anthropic client, it would default to https://api.anthropic.com.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    connector_entity.model_endpoint = ""

    anthropic_adapter.configure(connector_entity)

    assert isinstance(anthropic_adapter._client, AsyncAnthropic)
    assert anthropic_adapter._client.base_url == "https://api.anthropic.com"


@pytest.mark.parametrize("test_scenarios", [
    {
        "name": "no_max_token",
        "params": {},
        "expected_error_message": r"\[AnthropicAdapter\].\[configure\] Max tokens not specified/valid."
    },
    {
        "name": "invalid_max_token",
        "params": {"max_tokens": "one"},
        "expected_error_message": r"\[AnthropicAdapter\].\[configure\] Max tokens must be >=1, \"one\" provided."
    },
    {
        "name": "zero_max_token",
        "params": {"max_tokens": 0},
        "expected_error_message": r"\[AnthropicAdapter\].\[configure\] Max tokens must be >=1, \"0\" provided."
    },
    {
        "name": "less_than_one_max_token",
        "params": {"max_tokens": -1},
        "expected_error_message": r"\[AnthropicAdapter\].\[configure\] Max tokens must be >=1, \"-1\" provided."
    },
])
def test_configure_with_invalid_max_tokens(anthropic_adapter: AnthropicAdapter,
                                           connector_entity: ConnectorEntity,
                                           test_scenarios: dict):
    """
    Test configuration with no/invalid max tokens defined in params attribute, which Assert Error is thrown.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    connector_entity.params = test_scenarios["params"]

    with pytest.raises(AssertionError, match=test_scenarios["expected_error_message"]):
        anthropic_adapter.configure(connector_entity)


def test_configure_with_no_model(anthropic_adapter: AnthropicAdapter, connector_entity: ConnectorEntity):
    """
    Test configuration with empty model name as model name is a required parameter. Assert error is thrown if
    model is not specified.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    connector_entity.model = ""

    with pytest.raises(AssertionError, match=r"\[AnthropicAdapter\].\[configure\] Model not specified."):
        anthropic_adapter.configure(connector_entity)


# ================================
# Test getting prompt response with Anthropic Adapter
# ================================
@pytest.mark.asyncio
async def test_get_response_with_required_parameters(mock_anthropic_client: MagicMock,
                                                     anthropic_adapter: AnthropicAdapter,
                                                     connector_entity: ConnectorEntity):
    """
    Ensure model, max_tokens, and messages are included in the request parameters.

    Args:
        mock_anthropic_client: Mocked Anthropic client.
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class:
        mock_anthropic_class.return_value = mock_anthropic_client
        connector_entity.model = "test model name"

        anthropic_adapter.configure(connector_entity)
        await anthropic_adapter.get_response("Test prompt")
        result_params = mock_anthropic_client.messages.create.call_args.kwargs

        assert "model" in result_params
        assert "max_tokens" in result_params
        assert "messages" in result_params


@pytest.mark.asyncio
async def test_get_response_success_with_system_prompt(mock_anthropic_client: MagicMock,
                                                       anthropic_adapter: AnthropicAdapter,
                                                       connector_entity: ConnectorEntity):
    """
    Test successful response with system prompt.
    Will check if system prompt was included in the request parameters and content of reponse text.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class:
        mock_anthropic_class.return_value = mock_anthropic_client
        connector_entity.system_prompt = "You are a helpful assistant."

        anthropic_adapter.configure(connector_entity)
        result = await anthropic_adapter.get_response("Test prompt")
        result_system_prompt = mock_anthropic_client.messages.create.call_args.kwargs['system']
        result_prompt = mock_anthropic_client.messages.create.call_args.kwargs['messages']

        assert result_system_prompt == "You are a helpful assistant."
        assert result_prompt == [{"role": "user", "content": "Test prompt"}]
        assert isinstance(result, ConnectorResponseEntity) and result.response == "Test response from Anthropic client."


@pytest.mark.asyncio
async def test_get_response_success_without_system_prompt(mock_anthropic_client: MagicMock,
                                                          anthropic_adapter: AnthropicAdapter,
                                                          connector_entity: ConnectorEntity):
    """
    Test successful response without system prompt.
    Will check if system prompt is empty string in the request parameters and content of reponse
    text.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class:
        mock_anthropic_class.return_value = mock_anthropic_client

        connector_entity.system_prompt = ""

        anthropic_adapter.configure(connector_entity)
        result = await anthropic_adapter.get_response("Test prompt")
        result_system_prompt = mock_anthropic_client.messages.create.call_args.kwargs['system']
        result_prompt = mock_anthropic_client.messages.create.call_args.kwargs['messages']

        assert result_system_prompt == ""
        assert result_prompt == [{"role": "user", "content": "Test prompt"}]
        assert isinstance(result, ConnectorResponseEntity) and result.response == "Test response from Anthropic client."


@pytest.mark.asyncio
async def test_get_response_with_pre_post_prompts(mock_anthropic_client: MagicMock,
                                                  anthropic_adapter: AnthropicAdapter,
                                                  connector_entity: ConnectorEntity):
    """
    Test response with pre and post prompts.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class:
        mock_anthropic_class.return_value = mock_anthropic_client

        connector_entity.connector_pre_prompt = "<Pre>"
        connector_entity.connector_post_prompt = "<Post>"

        anthropic_adapter.configure(connector_entity)
        result = await anthropic_adapter.get_response("Test prompt")
        result_prompt = mock_anthropic_client.messages.create.call_args.kwargs['messages']

        expected_prompt = "<Pre>" + "Test prompt" + "<Post>"
        assert result_prompt == [{"role": "user", "content": expected_prompt}]
        assert isinstance(result, ConnectorResponseEntity) and result.response == "Test response from Anthropic client."


@pytest.mark.asyncio
async def test_get_response_with_valid_max_token(mock_anthropic_client: MagicMock,
                                                 anthropic_adapter: AnthropicAdapter,
                                                 connector_entity: ConnectorEntity):
    """
    Test configuration with >1 max tokens defined in params attribute.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class:
        mock_anthropic_class.return_value = mock_anthropic_client
        connector_entity.params = {"max_tokens": 10000}

        anthropic_adapter.configure(connector_entity)
        await anthropic_adapter.get_response("Test prompt")

        assert mock_anthropic_client.messages.create.call_args.kwargs['max_tokens'] == 10000


@pytest.mark.asyncio
async def test_get_response_additional_params(mock_anthropic_client: MagicMock,
                                              anthropic_adapter: AnthropicAdapter,
                                              connector_entity: ConnectorEntity):
    """
    Test response with additional Anthropic parameters.

    Args:
        anthropic_adapter: Anthropic adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class:
        mock_anthropic_class.return_value = mock_anthropic_client
        connector_entity.params["temperature"] = 0.6

        anthropic_adapter.configure(connector_entity)
        await anthropic_adapter.get_response("Test prompt")

        assert mock_anthropic_client.messages.create.call_args.kwargs['temperature'] == 0.6


# ================================
# Test function to check required parameters
# ================================
def test_is_all_required_params_present(anthropic_adapter: AnthropicAdapter):
    """
    Test the method that checks if all required parameters are present in the request.

    Args:
        None
    """
    required_params = ["model", "max_tokens", "messages"]

    # Happy flow: Test with all required parameters
    params = {"model": None, "max_tokens": None, "messages": None}
    assert AnthropicAdapter()._is_all_required_params_present(params, required_params) is True

    # Test with more given parameters than required parameters
    params = {"system": None, "model": None, "max_tokens": None, "messages": None}
    assert AnthropicAdapter()._is_all_required_params_present(params, required_params) is True

    # Test with missing required parameter
    params = {"max_tokens": None, "messages": None}
    assert AnthropicAdapter()._is_all_required_params_present(params, required_params) is False

    # Test with no required parameter
    params = {}
    assert AnthropicAdapter()._is_all_required_params_present(params, required_params) is False


# ================================
# Test exception handling in get_response
# ================================
@pytest.mark.asyncio
async def test_get_response_raises_api_connection_error(anthropic_adapter: AnthropicAdapter,
                                                        connector_entity: ConnectorEntity):
    """
    Test that get_response raises APIConnectionError and logs error.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class, \
            patch.object(adapters.connector.anthropic_adapter.logger, 'error') as mock_error_logger:

        # Arrange: mock AsyncAnthropic to raise APIConnectionError when create() is called.
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.APIConnectionError(message="Connection error.", request=None))
        mock_anthropic_class.return_value = mock_client

        # Act: call get_response and expect it to raise APIConnectionError.
        anthropic_adapter.configure(connector_entity)
        with pytest.raises(expected_exception=anthropic.APIConnectionError) as exception_info:
            await anthropic_adapter.get_response("Prompt")
        result_logger_error_string = mock_error_logger.call_args_list[0][0][0]

        # Assert: anthropic.APIConnectionError is raised and error is logged.
        expected_error_log = re.compile(r"\[AnthropicAdapter\].\[get_response\] The server could not be reached, "
                                        + r"cause: \"%s\", stack trace: \"%s\"")
        assert expected_error_log.match(result_logger_error_string)
        assert exception_info.value.message == "Connection error."


@pytest.mark.asyncio
@pytest.mark.parametrize("test_scenarios", [
    {"status_code": 400, "exception_class": anthropic.BadRequestError},
    {"status_code": 401, "exception_class": anthropic.AuthenticationError},
    {"status_code": 403, "exception_class": anthropic.PermissionDeniedError},
    {"status_code": 404, "exception_class": anthropic.NotFoundError},
    {"status_code": 422, "exception_class": anthropic.UnprocessableEntityError},
    {"status_code": 429, "exception_class": anthropic.RateLimitError},
    {"status_code": 500, "exception_class": anthropic.InternalServerError},
])
async def test_get_response_raises_http_related_error(anthropic_adapter: AnthropicAdapter,
                                                      connector_entity: ConnectorEntity,
                                                      test_scenarios: dict):
    """
    Test that get_response raises HTTP related error and logs error.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class, \
            patch.object(adapters.connector.anthropic_adapter.logger, 'error') as mock_error_logger:

        # Arrange: mock AsyncAnthropic to raise APIConnectionError when create() is called.
        mock_response = MagicMock()
        mock_response.status_code = test_scenarios["status_code"]
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            side_effect=test_scenarios["exception_class"](message=None, response=mock_response, body=None))
        mock_anthropic_class.return_value = mock_client

        # Act: call get_response and expect it to raise APIConnectionError.
        anthropic_adapter.configure(connector_entity)
        with pytest.raises(expected_exception=test_scenarios["exception_class"]) as exception_info:
            await anthropic_adapter.get_response("Prompt")
        result_logger_error_string = mock_error_logger.call_args_list[0][0][0]

        # Assert: anthropic.APIConnectionError is raised and error is logged.
        expected_error_log = re.compile(r"\[AnthropicAdapter\].\[get_response\] Error getting a reponse from Anthropic,"
                                        + r" status code: \"%s\", response: \"%s\", stack trace: \"%s\"")
        assert expected_error_log.match(result_logger_error_string)
        assert exception_info.value.status_code == test_scenarios["status_code"]


@pytest.mark.asyncio
async def test_get_response_raises_exception(anthropic_adapter: AnthropicAdapter,
                                             connector_entity: ConnectorEntity):
    """
    Test that get_response raises Exception and logs error.
    """
    with patch('adapters.connector.anthropic_adapter.AsyncAnthropic') as mock_anthropic_class, \
            patch.object(adapters.connector.anthropic_adapter.logger, 'error') as mock_error_logger:

        # Arrange: mock AsyncAnthropic to raise APIConnectionError when create() is called.
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            side_effect=Exception("Something went wrong."))
        mock_anthropic_class.return_value = mock_client

        # Act: call get_response and expect it to raise APIConnectionError.
        anthropic_adapter.configure(connector_entity)
        with pytest.raises(expected_exception=Exception) as exception_info:
            await anthropic_adapter.get_response("Prompt")
        result_logger_error_string = mock_error_logger.call_args_list[0][0][0]

        # Assert: anthropic.APIConnectionError is raised and error is logged.
        print(result_logger_error_string)
        expected_error_log = re.compile(r"\[AnthropicAdapter\].\[get_response\] Error processing prompt, "
                                        + r"stack trace: %s")
        assert expected_error_log.match(result_logger_error_string)
        assert str(exception_info.value) == "Something went wrong."
