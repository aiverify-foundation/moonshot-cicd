import aiohttp
import pytest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from adapters.connector.aws_sagemaker_adapter import AWSSageMakerAdapter
from domain.entities.connector_entity import ConnectorEntity


class CoroutineMock:
    """Helper class to mock coroutines for testing."""
    
    def __init__(self, return_value=None, side_effect=None):
        self.return_value = return_value
        self.side_effect = side_effect

    async def __call__(self, *args, **kwargs):
        if self.side_effect:
            raise self.side_effect
        return self.return_value


@pytest.fixture
def connector_entity():
    """
    Create a test connector entity for AWS SageMaker.
    
    Returns:
        ConnectorEntity: A configured connector entity for testing.
    """
    return ConnectorEntity(
        connector_adapter="aws_sagemaker",
        model="my-sagemaker-endpoint",
        model_endpoint="",
        params={
            "session": {
                "region_name": "us-east-1"
            },
            "temperature": 0.7,
            "max_tokens": 1000
        },
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt="You are a helpful assistant."
    )

@pytest.fixture
def sagemaker_adapter():
    """
    Create an AWS SageMaker adapter instance.
    
    Returns:
        AWSSageMakerAdapter: A fresh adapter instance for testing.
    """
    return AWSSageMakerAdapter()

# ================================
# Test configure
# ================================
def test_configure_none_params(sagemaker_adapter, connector_entity):
    """
    Test handling when params is None.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
    """
    with pytest.raises(ValueError, match=AWSSageMakerAdapter.ERROR_MISSING_CONNECTOR_ENTITY):
        sagemaker_adapter.configure(None)
        
        assert sagemaker_adapter.connector_entity is None
        assert sagemaker_adapter.aws_region is None
        assert sagemaker_adapter.aws_model is None


def test_configure_empty_params(sagemaker_adapter, connector_entity):
    """
    Test handling when params is empty.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
    """
    connector_entity.params = {}
    sagemaker_adapter.configure(connector_entity)

    assert sagemaker_adapter.connector_entity == connector_entity
    assert sagemaker_adapter.aws_region == "ap-southeast-1"
    assert sagemaker_adapter.aws_model == "my-sagemaker-endpoint"


def test_configure_empty_model(sagemaker_adapter, connector_entity):
    """
    Test handling when model is empty.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
    """
    connector_entity.model = ""
    with pytest.raises(ValueError, match=AWSSageMakerAdapter.ERROR_MISSING_ENDPOINT):
        sagemaker_adapter.configure(connector_entity)

        assert sagemaker_adapter.connector_entity is None
        assert sagemaker_adapter.aws_region is None
        assert sagemaker_adapter.aws_model is None


def test_configure_success(sagemaker_adapter, connector_entity):
    """
    Test successful configuration of the adapter.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
    """
    with patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        sagemaker_adapter.configure(connector_entity)
        
        assert sagemaker_adapter.connector_entity == connector_entity
        assert sagemaker_adapter.aws_region == "us-east-1"
        assert sagemaker_adapter.aws_model == "my-sagemaker-endpoint"
        
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args.args[0] == (
            f"Configured AWS SageMaker adapter with region: {sagemaker_adapter.aws_region} and model name: {sagemaker_adapter.aws_model}"
        )

def test_configure_exception_handling(sagemaker_adapter, connector_entity):
    """
    Test configuration exception handling.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
    """
    # Set model to None to trigger error
    connector_entity.model = None
    
    with patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        with pytest.raises(ValueError, match=AWSSageMakerAdapter.ERROR_MISSING_ENDPOINT):
            sagemaker_adapter.configure(connector_entity)
        
        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args.args[0] == "Could not set up connection to the AI model: The AI model endpoint was not specified in the settings."

# ================================
# Test process_response
# ================================
@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", [
    {
        "name": "success_with_content",
        "response": {
            "choices": [{
                "message": {
                    "content": "Processed response"
                }
            }]
        },
        "expected_result": "Processed response"
    },
    {
        "name": "success_empty_content", 
        "response": {
            "choices": [{
                "message": {
                    "content": ""
                }
            }]
        },
        "expected_result": ""
    },
    {
        "name": "success_multiple_choices",
        "response": {
            "choices": [
                {
                    "message": {
                        "content": "First response"
                    }
                },
                {
                    "message": {
                        "content": "Second response" 
                    }
                }
            ]
        },
        "expected_result": "First response"
    },
    {
        "name": "numeric_content",
        "response": {"choices": [{"message": {"content": "12345"}}]},
        "expected_result": "12345"
    },
    {
        "name": "numeric_array_content",
        "response": {"choices": [{"message": {"content": "[1, 2, 3, 4, 5]"}}]},
        "expected_result": "[1, 2, 3, 4, 5]"
    },
    {
        "name": "float_content",
        "response": {"choices": [{"message": {"content": "3.14159"}}]},
        "expected_result": "3.14159"
    },
    {
        "name": "zero_content",
        "response": {"choices": [{"message": {"content": "0"}}]},
        "expected_result": "0"
    }
])
async def test_process_response_success_cases(sagemaker_adapter, test_case):
    """
    Test successful response processing scenarios.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        test_case: Parametrized test case data containing response and expected result.
    """
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=test_case["response"])

    with patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        result = await sagemaker_adapter._process_response(mock_response)
        assert result == test_case["expected_result"]
        
        mock_logger.info.assert_called_once_with(
            AWSSageMakerAdapter.LOG_PROCESSING_RESPONSE
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", [
    {
        "name": "empty_response", 
        "response": {},
        "raw_text": "empty response",
        "error": AWSSageMakerAdapter.ERROR_EMPTY_RESPONSE,
    },
    {
        "name": "none_response",
        "response": None,
        "raw_text": "none response", 
        "error": AWSSageMakerAdapter.ERROR_EMPTY_RESPONSE,
    },
    {
        "name": "missing_choices",
        "response": {"some_field": "value"},
        "raw_text": "invalid response",
        "error": AWSSageMakerAdapter.ERROR_MISSING_CHOICES
    },
    {
        "name": "empty_choices",
        "response": {"choices": []},
        "raw_text": "empty choices", 
        "error": AWSSageMakerAdapter.ERROR_NO_CHOICES
    },
    {
        "name": "none_choices",
        "response": {"choices": None},
        "raw_text": "none choices",
        "error": AWSSageMakerAdapter.ERROR_NO_CHOICES
    },
    {
        "name": "missing_message",
        "response": {"choices": [{"some_field": "value"}]},
        "raw_text": "missing message",
        "error": AWSSageMakerAdapter.ERROR_MISSING_MESSAGE
    },
    {
        "name": "none_message",
        "response": {"choices": [{"message": None}]},
        "raw_text": "none message",
        "error": AWSSageMakerAdapter.ERROR_MISSING_MESSAGE
    },
    {
        "name": "missing_content",
        "response": {"choices": [{"message": {"role": "assistant"}}]},
        "raw_text": "missing content",
        "error": AWSSageMakerAdapter.ERROR_MISSING_CONTENT
    },
    {
        "name": "none_content", 
        "response": {"choices": [{"message": {"content": None}}]},
        "raw_text": "none content",
        "error": AWSSageMakerAdapter.ERROR_MISSING_CONTENT
    },
    {
        "name": "malformed_choices",
        "response": {"choices": {}},
        "raw_text": "malformed choices",
        "error": AWSSageMakerAdapter.ERROR_NO_CHOICES
    },
    {
        "name": "multiple_choices_with_invalid_first",
        "response": {
            "choices": [
                {"message": None},
                {"message": {"content": "valid but second"}}
            ]
        },
        "raw_text": "multiple choices first invalid",
        "error": AWSSageMakerAdapter.ERROR_MISSING_MESSAGE
    },
])
async def test_process_response_errors(sagemaker_adapter, test_case):
    """
    Test processing of response with various errors.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        test_case: Parametrized test case data containing response, raw text and expected error.
    """
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=test_case["response"])
    mock_response.text = AsyncMock(return_value=test_case["raw_text"])
    
    with patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        with pytest.raises(ValueError, match=test_case["error"]):
            await sagemaker_adapter._process_response(mock_response)
        
        mock_logger.error.assert_called_once()
        error_msg = test_case["error"]
        assert mock_logger.error.call_args.args[0] == (
            f"Problem processing the AI model's response: {error_msg} Raw response: {test_case['raw_text']}"
        )

@pytest.mark.asyncio
async def test_process_response_unexpected_error(sagemaker_adapter):
    """
    Test processing of response with unexpected error.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
    """
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(side_effect=Exception("Unexpected error"))
    mock_response.text = AsyncMock(return_value="error response")

    with patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        with pytest.raises(Exception):
            await sagemaker_adapter._process_response(mock_response)
        
        mock_logger.error.assert_called_once_with(
            AWSSageMakerAdapter.ERROR_UNEXPECTED_PROCESSING.format("Unexpected error")
        )

# ================================
# Test get_response
# ================================
@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", [
    {
        "name": "empty_prompt",
        "prompt": "",
        "error": AWSSageMakerAdapter.ERROR_EMPTY_PROMPT,
        "exception_type": ValueError,
        "exception_log_message": "Problem getting response from the AI model: No text was provided to process."
    },
    {
        "name": "none_prompt", 
        "prompt": None,
        "error": AWSSageMakerAdapter.ERROR_EMPTY_PROMPT,
        "exception_type": ValueError,
        "exception_log_message": "Problem getting response from the AI model: No text was provided to process."
    }
])
async def test_get_response_validation_errors(sagemaker_adapter, connector_entity, test_case):
    """
    Test input validation error handling in get_response.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
        test_case: Parametrized test case data containing prompt, error and exception details.
    """
    sagemaker_adapter.configure(connector_entity)

    with patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        with pytest.raises(test_case["exception_type"]) as exc_info:
            await sagemaker_adapter.get_response(test_case["prompt"])

        assert str(exc_info.value) == test_case["error"]
        assert mock_logger.error.call_args.args[0] == test_case["exception_log_message"]
        mock_logger.error.assert_called()

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", [
    {
        "name": "basic_request",
        "prompt": "Test prompt",
        "system_prompt": None,
        "params": None,
        "expected_payload": {
            "messages": [
                {"role": "user", "content": "Test prompt"}
            ]
        }
    },
    {
        "name": "with_system_prompt",
        "prompt": "Test prompt",
        "system_prompt": "You are a helpful assistant",
        "params": None,
        "expected_payload": {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Test prompt"}
            ]
        }
    },
    {
        "name": "with_params",
        "prompt": "Test prompt",
        "system_prompt": None,
        "params": {"temperature": 0.7, "max_tokens": 100},
        "expected_payload": {
            "messages": [
                {"role": "user", "content": "Test prompt"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
    }
])
async def test_get_response_aws_error(sagemaker_adapter, connector_entity, test_case):
    """
    Test AWS request error handling in get_response with different payload configurations.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
        test_case: Parametrized test case data containing prompt, system prompt, params and expected payload.
    """
    import json

    # Configure connector entity based on test case
    connector_entity.system_prompt = test_case["system_prompt"]
    connector_entity.params = test_case["params"]
    connector_entity.connector_pre_prompt = ""  # Empty for test simplicity
    connector_entity.connector_post_prompt = ""
    sagemaker_adapter.configure(connector_entity)

    expected_url = f"https://runtime.sagemaker.{sagemaker_adapter.aws_region}.amazonaws.com/endpoints/{sagemaker_adapter.aws_model}/invocations"
    expected_headers = {"Content-Type": "application/json"}

    with patch('adapters.connector.aws_sagemaker_adapter.AWSRequest') as mock_aws_request, \
        patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        
        error_message = "AWS Request failed"
        mock_aws_request.side_effect = Exception(error_message)

        with pytest.raises(Exception) as exc_info:
            await sagemaker_adapter.get_response(test_case["prompt"])

        mock_aws_request.assert_called_once_with(
            method="POST",
            url=expected_url,
            data=json.dumps(test_case["expected_payload"]),
            headers=expected_headers
        )

        assert str(exc_info.value) == error_message
        assert mock_logger.error.call_args.args[0] == f"An unexpected error occurred while getting the response: {error_message}"
        mock_logger.error.assert_called()

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", [
    {
        "name": "session_is_none",
        "session_return": None,
        "get_credentials_return": None,  # Not used when session is None
        "expected_error": AWSSageMakerAdapter.ERROR_INVALID_SESSION,
        "expected_log": "Problem getting response from the AI model: AWS Session could not be initialized."
    },
    {
        "name": "get_credentials_returns_none",
        "session_return": MagicMock(),
        "get_credentials_return": None,
        "expected_error": AWSSageMakerAdapter.ERROR_MISSING_CREDENTIALS,
        "expected_log": "Problem getting response from the AI model: Could not find AWS login details."
    },
    {
        "name": "get_credentials_returns_empty_string",
        "session_return": MagicMock(),
        "get_credentials_return": "",
        "expected_error": AWSSageMakerAdapter.ERROR_MISSING_CREDENTIALS,
        "expected_log": "Problem getting response from the AI model: Could not find AWS login details."
    },
    {
        "name": "get_credentials_returns_empty_dict",
        "session_return": MagicMock(),
        "get_credentials_return": {},
        "expected_error": AWSSageMakerAdapter.ERROR_MISSING_CREDENTIALS,
        "expected_log": "Problem getting response from the AI model: Could not find AWS login details."
    },
    {
        "name": "get_credentials_returns_empty_list",
        "session_return": MagicMock(),
        "get_credentials_return": [],
        "expected_error": AWSSageMakerAdapter.ERROR_MISSING_CREDENTIALS,
        "expected_log": "Problem getting response from the AI model: Could not find AWS login details."
    },
    {
        "name": "get_credentials_returns_false",
        "session_return": MagicMock(),
        "get_credentials_return": False,
        "expected_error": AWSSageMakerAdapter.ERROR_MISSING_CREDENTIALS,
        "expected_log": "Problem getting response from the AI model: Could not find AWS login details."
    },
    {
        "name": "get_credentials_returns_zero",
        "session_return": MagicMock(),
        "get_credentials_return": 0,
        "expected_error": AWSSageMakerAdapter.ERROR_MISSING_CREDENTIALS,
        "expected_log": "Problem getting response from the AI model: Could not find AWS login details."
    }
])
async def test_get_response_credentials_validation_errors(sagemaker_adapter, connector_entity, test_case):
    """
    Test various credential validation error cases in get_response.
    
    Args:
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
        test_case: Parametrized test case data containing session returns, expected errors and logs.
    """
    sagemaker_adapter.configure(connector_entity)

    with patch('adapters.connector.aws_sagemaker_adapter.Session') as mock_session, \
         patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:

        mock_session.return_value = test_case["session_return"]
        if test_case["session_return"] is not None:
            mock_session.return_value.get_credentials.return_value = test_case["get_credentials_return"]

        with pytest.raises(ValueError) as exc_info:
            await sagemaker_adapter.get_response("Test prompt")

        # Verify the exception message
        assert str(exc_info.value) == test_case["expected_error"]
        
        # Verify the logging message
        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args.args[0] == test_case["expected_log"]


@pytest.mark.asyncio
@patch('adapters.connector.aws_sagemaker_adapter.aiohttp.ClientSession.post')
async def test_get_response_success(mock_post, sagemaker_adapter, connector_entity):
    """
    Test successful response retrieval from AWS SageMaker.
    
    This is a simplified version of success test focusing on the key mocking points.
    
    Args:
        mock_post: Mocked aiohttp ClientSession.post method.
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
    """
    
    sagemaker_adapter.configure(connector_entity)
    
    # Mock all the AWS components
    mock_credentials = MagicMock()
    mock_session = MagicMock()
    mock_session.get_credentials.return_value = mock_credentials
    mock_request = MagicMock()
    mock_auth = MagicMock()
    
    # Mock the HTTP response
    mock_http_response = AsyncMock()
    
    # Set up aiohttp mocking
    mock_post.return_value.__aenter__.return_value = mock_http_response
    mock_post.return_value.__aenter__ = CoroutineMock(mock_http_response)
    mock_post.return_value.__aexit__ = CoroutineMock(None)
    
    with patch('adapters.connector.aws_sagemaker_adapter.Session', return_value=mock_session), \
        patch('adapters.connector.aws_sagemaker_adapter.AWSRequest', return_value=mock_request), \
        patch('adapters.connector.aws_sagemaker_adapter.SigV4Auth', return_value=mock_auth), \
        patch.object(sagemaker_adapter, '_process_response', return_value="Processed Response") as mock_process_response:
        
        # Execute the test
        result = await sagemaker_adapter.get_response("Test prompt")
        
        # Basic verification
        assert result.response == "Processed Response"
        mock_process_response.assert_called_once_with(mock_http_response)
        mock_auth.add_auth.assert_called_once_with(mock_request)


@pytest.mark.asyncio
@patch('adapters.connector.aws_sagemaker_adapter.aiohttp.ClientSession.post')
async def test_get_response_aiohttp_client_error(mock_post, sagemaker_adapter, connector_entity):
    """
    Test that aiohttp.ClientError is properly handled and logged.
    
    Args:
        mock_post: Mocked aiohttp ClientSession.post method.
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
    """
    
    sagemaker_adapter.configure(connector_entity)
    
    # Mock all the AWS components
    mock_credentials = MagicMock()
    mock_session = MagicMock()
    mock_session.get_credentials.return_value = mock_credentials
    mock_request = MagicMock()
    mock_auth = MagicMock()
    
    # Mock aiohttp to raise ClientError
    mock_client_error = aiohttp.ClientError("Connection failed")
    mock_post.return_value.__aenter__ = CoroutineMock(side_effect=mock_client_error)
    mock_post.return_value.__aexit__ = CoroutineMock(None)
    
    with patch('adapters.connector.aws_sagemaker_adapter.Session', return_value=mock_session), \
        patch('adapters.connector.aws_sagemaker_adapter.AWSRequest', return_value=mock_request), \
        patch('adapters.connector.aws_sagemaker_adapter.SigV4Auth', return_value=mock_auth), \
        patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        
        # Execute and verify error handling
        with pytest.raises(aiohttp.ClientError) as exc_info:
            await sagemaker_adapter.get_response("Test prompt")
        
        # Verify the correct exception was raised
        assert str(exc_info.value) == "Connection failed"
        
        # Verify error was logged with the correct message
        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args.args[0] == sagemaker_adapter.ERROR_GET_RESPONSE.format("Connection failed")


@pytest.mark.asyncio
@patch('adapters.connector.aws_sagemaker_adapter.aiohttp.ClientSession.post')
async def test_get_response_aiohttp_timeout_error(mock_post, sagemaker_adapter, connector_entity):
    """
    Test that aiohttp.ServerTimeoutError is properly handled and logged.
    
    Args:
        mock_post: Mocked aiohttp ClientSession.post method.
        sagemaker_adapter: AWS SageMaker adapter instance.
        connector_entity: Test connector entity.
    """
    
    sagemaker_adapter.configure(connector_entity)
    
    # Mock all the AWS components
    mock_credentials = MagicMock()
    mock_session = MagicMock()
    mock_session.get_credentials.return_value = mock_credentials
    mock_request = MagicMock()
    mock_auth = MagicMock()
    
    # Mock aiohttp to raise ServerTimeoutError (which is a subclass of ClientError)
    mock_timeout_error = aiohttp.ServerTimeoutError("Request timeout")
    mock_post.return_value.__aenter__ = CoroutineMock(side_effect=mock_timeout_error)
    mock_post.return_value.__aexit__ = CoroutineMock(None)
    
    with patch('adapters.connector.aws_sagemaker_adapter.Session', return_value=mock_session), \
        patch('adapters.connector.aws_sagemaker_adapter.AWSRequest', return_value=mock_request), \
        patch('adapters.connector.aws_sagemaker_adapter.SigV4Auth', return_value=mock_auth), \
        patch('adapters.connector.aws_sagemaker_adapter.logger') as mock_logger:
        
        # Execute and verify error handling
        with pytest.raises(aiohttp.ServerTimeoutError) as exc_info:
            await sagemaker_adapter.get_response("Test prompt")
        
        # Verify the correct exception was raised
        assert str(exc_info.value) == "Request timeout"
        
        # Verify error was logged with the correct message format
        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args.args[0] == sagemaker_adapter.ERROR_GET_RESPONSE.format("Request timeout")
