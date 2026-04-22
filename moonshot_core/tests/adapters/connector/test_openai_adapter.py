"""
Tests for the OpenAIAdapter class.

This module contains comprehensive tests for the OpenAIAdapter class, which handles
communication with OpenAI's API for chat completions using AsyncOpenAI client.
"""

import os
import pytest
from unittest.mock import AsyncMock, patch, Mock, MagicMock, ANY
from openai import BadRequestError

from adapters.connector.openai_adapter import OpenAIAdapter
from domain.entities.connector_entity import ConnectorEntity


@pytest.fixture
def connector_entity():
    """
    Create a test connector entity for OpenAI.
    
    Returns:
        ConnectorEntity: A test connector entity with complete OpenAI configuration.
    """
    return ConnectorEntity(
        connector_adapter="openai",
        model="gpt-4",
        model_endpoint="https://api.openai.com/v1",
        params={
            "temperature": 0.7,
            "max_tokens": 1000
        },
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt="You are a helpful assistant."
    )

@pytest.fixture
def openai_adapter():
    """
    Create an OpenAI adapter instance.
    
    Returns:
        OpenAIAdapter: A fresh OpenAI adapter instance for testing.
    """
    return OpenAIAdapter()

# ================================
# Test configure
# ================================
def test_configure_with_api_key_and_endpoint(openai_adapter, connector_entity):
    """
    Test successful configuration with API key and custom endpoint.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.openai_adapter.AsyncOpenAI') as mock_openai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        openai_adapter.configure(connector_entity)
        
        assert openai_adapter.connector_entity == connector_entity
        assert openai_adapter._client == mock_client
        
        # Verify AsyncOpenAI was called with correct parameters
        mock_openai_class.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://api.openai.com/v1"
        )

def test_configure_with_empty_api_key(openai_adapter, connector_entity):
    """
    Test configuration with empty API key.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.openai_adapter.AsyncOpenAI') as mock_openai_class:
        
        mock_getenv.return_value = None
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        openai_adapter.configure(connector_entity)
        
        # Verify AsyncOpenAI was called with fallback API key when env var is None
        # Using ANY to check that api_key exists without asserting its exact value
        mock_openai_class.assert_called_once_with(
            api_key=ANY,  # Check that api_key exists, but don't care about its value
            base_url="https://api.openai.com/v1"
        )

def test_configure_with_no_endpoint(openai_adapter, connector_entity):
    """
    Test configuration with no model endpoint.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    connector_entity.model_endpoint = ""
    
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.openai_adapter.AsyncOpenAI') as mock_openai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        openai_adapter.configure(connector_entity)
        
        # Verify AsyncOpenAI was called with None for base_url
        mock_openai_class.assert_called_once_with(
            api_key="test-api-key",
            base_url=None
        )

# ================================
# Test _process_response
# ================================
@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", [
    {
        "name": "simple_response",
        "response_content": "This is a test response",
        "expected_result": "This is a test response"
    },
    {
        "name": "empty_response",
        "response_content": "",
        "expected_result": ""
    },
    {
        "name": "none_content",
        "response_content": None,
        "expected_result": None
    }
])
async def test_process_response_success_cases(openai_adapter, test_case):
    """
    Test successful response processing scenarios.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        test_case: Parameterized test case data.
    """
    # Create mock response object
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = test_case["response_content"]
    
    result = await openai_adapter._process_response(mock_response)
    assert result == test_case["expected_result"]

@pytest.mark.asyncio
async def test_process_response_missing_choices(openai_adapter):
    """
    Test processing response with missing choices.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
    """
    mock_response = MagicMock()
    mock_response.choices = []
    
    with pytest.raises(IndexError):
        await openai_adapter._process_response(mock_response)

# ================================
# Test get_response
# ================================
@pytest.mark.asyncio
async def test_get_response_success_with_system_prompt(openai_adapter, connector_entity):
    """
    Test successful response with system prompt.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    # Create mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Test response"
    
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.openai_adapter.AsyncOpenAI') as mock_openai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        openai_adapter.configure(connector_entity)
        result = await openai_adapter.get_response("Test prompt")
        
        assert result.response == "Test response"
        
        # Check messages structure with system prompt
        call_args = mock_client.chat.completions.create.call_args.kwargs
        expected_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test prompt"}
        ]
        assert call_args["messages"] == expected_messages

@pytest.mark.asyncio
async def test_get_response_success_without_system_prompt(openai_adapter, connector_entity):
    """
    Test successful response without system prompt.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    connector_entity.system_prompt = ""
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Test response"
    
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.openai_adapter.AsyncOpenAI') as mock_openai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        openai_adapter.configure(connector_entity)
        result = await openai_adapter.get_response("Test prompt")
        
        # Check messages structure without system prompt
        call_args = mock_client.chat.completions.create.call_args.kwargs
        expected_messages = [
            {"role": "user", "content": "Test prompt"}
        ]
        assert call_args["messages"] == expected_messages

@pytest.mark.asyncio
async def test_get_response_with_pre_post_prompts(openai_adapter, connector_entity):
    """
    Test response with pre and post prompts.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    connector_entity.connector_pre_prompt = "Pre: "
    connector_entity.connector_post_prompt = " :Post"
    connector_entity.system_prompt = ""
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Test response"
    
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.openai_adapter.AsyncOpenAI') as mock_openai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        openai_adapter.configure(connector_entity)
        result = await openai_adapter.get_response("Test")
        
        # Check that pre and post prompts were applied
        call_args = mock_client.chat.completions.create.call_args.kwargs
        expected_messages = [
            {"role": "user", "content": "Pre: Test :Post"}
        ]
        assert call_args["messages"] == expected_messages

@pytest.mark.asyncio
async def test_get_response_api_exception(openai_adapter, connector_entity):
    """
    Test handling of OpenAI API exceptions.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.openai_adapter.AsyncOpenAI') as mock_openai_class, \
         patch('adapters.connector.openai_adapter.logger') as mock_logger:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Simulate OpenAI API exception
        api_error = Exception("OpenAI API error")
        mock_client.chat.completions.create = AsyncMock(side_effect=api_error)
        
        openai_adapter.configure(connector_entity)
        
        with pytest.raises(Exception) as exc_info:
            await openai_adapter.get_response("Test prompt")
        
        assert str(exc_info.value) == "OpenAI API error"
        
        # Verify error logging
        mock_logger.error.assert_called_once()
        assert OpenAIAdapter.ERROR_PROCESSING_PROMPT in mock_logger.error.call_args.args[0]


@pytest.mark.asyncio
async def test_get_response_strips_api_type_from_create_kwargs(openai_adapter, connector_entity):
    """DB/YAML merges may include api_type; it must not be passed to the SDK."""
    connector_entity.params = {"api_type": "openai", "temperature": 0.2}
    connector_entity.system_prompt = ""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "ok"

    with patch("adapters.connector.openai_adapter.os.getenv") as mock_getenv, patch(
        "adapters.connector.openai_adapter.AsyncOpenAI"
    ) as mock_openai_class:
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        openai_adapter.configure(connector_entity)
        await openai_adapter.get_response("Hi")

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "api_type" not in kwargs
        assert kwargs.get("temperature") == 0.2


@pytest.mark.asyncio
async def test_get_response_coerces_string_temperature_to_float(
    openai_adapter, connector_entity
):
    """Relational DB stores numeric params as strings; SDK must receive a float."""
    connector_entity.params = {"api_type": "openai", "temperature": "0.2", "max_tokens": "100"}
    connector_entity.system_prompt = ""

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "ok"

    with patch("adapters.connector.openai_adapter.os.getenv") as mock_getenv, patch(
        "adapters.connector.openai_adapter.AsyncOpenAI"
    ) as mock_openai_class:
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        openai_adapter.configure(connector_entity)
        await openai_adapter.get_response("Hi")

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs.get("temperature") == 0.2
        assert isinstance(kwargs.get("temperature"), float)
        assert kwargs.get("max_tokens") == 100
        assert isinstance(kwargs.get("max_tokens"), int)


@pytest.mark.asyncio
async def test_get_response_additional_params(openai_adapter, connector_entity):
    """
    Test response with additional OpenAI parameters.
    
    Args:
        openai_adapter: OpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    connector_entity.params = {
        "temperature": 0.9,
        "max_tokens": 2000,
        "top_p": 0.8
    }
    connector_entity.system_prompt = ""
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Response with params"
    
    with patch('adapters.connector.openai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.openai_adapter.AsyncOpenAI') as mock_openai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        openai_adapter.configure(connector_entity)
        result = await openai_adapter.get_response("Test")
        
        # Verify all parameters were passed through
        call_args = mock_client.chat.completions.create.call_args.kwargs
        assert call_args["temperature"] == 0.9
        assert call_args["max_tokens"] == 2000
        assert call_args["top_p"] == 0.8
        assert call_args["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_get_response_logs_on_unexpected_keyword_typeerror(
    openai_adapter, connector_entity
):
    connector_entity.params = {"temperature": 0.1}
    connector_entity.system_prompt = ""

    with (
        patch("adapters.connector.openai_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openai_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openai_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            side_effect=TypeError("got an unexpected keyword argument 'bad_key'")
        )

        openai_adapter.configure(connector_entity)
        with pytest.raises(TypeError):
            await openai_adapter.get_response("Hi")

        mock_logger.error.assert_called_once()
        logged = mock_logger.error.call_args.args[0]
        assert OpenAIAdapter.LOG_UNSUPPORTED_CHAT_KWARG in logged
        assert "unexpected keyword argument" in logged.lower()
        assert "connector_param_keys=" in logged


@pytest.mark.asyncio
async def test_get_response_logs_on_bad_request_error(openai_adapter, connector_entity):
    connector_entity.system_prompt = ""
    mock_response = MagicMock()
    mock_response.status_code = 400
    err = BadRequestError(
        "invalid parameter",
        response=mock_response,
        body={"error": {"message": "invalid"}},
    )

    with (
        patch("adapters.connector.openai_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openai_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openai_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=err)

        openai_adapter.configure(connector_entity)
        with pytest.raises(BadRequestError):
            await openai_adapter.get_response("Hi")

        mock_logger.error.assert_called_once()
        logged = mock_logger.error.call_args.args[0]
        assert OpenAIAdapter.LOG_API_REJECTED_CHAT in logged
        assert "invalid parameter" in logged


@pytest.mark.asyncio
async def test_get_response_logs_generic_on_runtime_error(
    openai_adapter, connector_entity
):
    connector_entity.system_prompt = ""

    with (
        patch("adapters.connector.openai_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openai_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openai_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("network"))

        openai_adapter.configure(connector_entity)
        with pytest.raises(RuntimeError, match="network"):
            await openai_adapter.get_response("Hi")

        mock_logger.error.assert_called_once()
        assert OpenAIAdapter.ERROR_PROCESSING_PROMPT in mock_logger.error.call_args.args[0]


@pytest.mark.asyncio
async def test_get_response_typeerror_without_unexpected_keyword_uses_generic_log(
    openai_adapter, connector_entity
):
    """TypeError that does not match the unexpected-kwarg heuristic uses generic logging."""
    connector_entity.system_prompt = ""

    with (
        patch("adapters.connector.openai_adapter.os.getenv") as mock_getenv,
        patch("adapters.connector.openai_adapter.AsyncOpenAI") as mock_openai_class,
        patch("adapters.connector.openai_adapter.logger") as mock_logger,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            side_effect=TypeError("unsupported operand type(s)")
        )

        openai_adapter.configure(connector_entity)
        with pytest.raises(TypeError, match="unsupported operand"):
            await openai_adapter.get_response("Hi")

        mock_logger.error.assert_called_once()
        logged = mock_logger.error.call_args.args[0]
        assert OpenAIAdapter.ERROR_PROCESSING_PROMPT in logged
        assert OpenAIAdapter.LOG_UNSUPPORTED_CHAT_KWARG not in logged