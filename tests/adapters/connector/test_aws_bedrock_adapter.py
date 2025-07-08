import asyncio
import pytest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from botocore.config import Config
from adapters.connector.aws_bedrock_adapter import AWSBedrockAdapter
from domain.entities.connector_entity import ConnectorEntity


@pytest.fixture
def connector_entity():
    """
    Create a test connector entity for AWS Bedrock.
    
    Returns:
        ConnectorEntity: A test connector entity with complete AWS Bedrock configuration.
    """
    return ConnectorEntity(
        connector_adapter="aws_bedrock",
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        model_endpoint="https://bedrock-runtime.us-east-1.amazonaws.com",
        params={
            "session": {
                "region_name": "us-east-1",
                "aws_access_key_id": "test_key",
                "aws_secret_access_key": "test_secret"
            },
            "client": {
                "config": {
                    "retries": {"max_attempts": 3}
                }
            },
            "inferenceConfig": {
                "temperature": 0.7,
                "maxTokens": 1000
            }
        },
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt=""
    )


@pytest.fixture
def bedrock_adapter():
    """
    Create an AWS Bedrock adapter instance.
    
    Returns:
        AWSBedrockAdapter: A fresh AWS Bedrock adapter instance for testing.
    """
    return AWSBedrockAdapter()


# ================================
# Test configure
# ================================
def test_configure_basic_success(bedrock_adapter, connector_entity):
    """
    Test successful basic configuration of the adapter.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        bedrock_adapter.configure(connector_entity)
        
        assert bedrock_adapter.connector_entity == connector_entity
        assert bedrock_adapter._session == mock_session
        assert bedrock_adapter._client == mock_client
        
        # Verify session was created with correct params
        mock_session_class.assert_called_once_with(
            region_name="us-east-1",
            aws_access_key_id="test_key", 
            aws_secret_access_key="test_secret"
        )
        
        # Verify client was created with bedrock-runtime service
        mock_session.client.assert_called_once()
        args, kwargs = mock_session.client.call_args
        assert args[0] == "bedrock-runtime"


def test_configure_with_config_object(bedrock_adapter, connector_entity):
    """
    Test configuration with Config object conversion.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.Config') as mock_config_class:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_config = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_config_class.return_value = mock_config
        
        bedrock_adapter.configure(connector_entity)
        
        # Verify Config was created from the config dict
        mock_config_class.assert_called_once_with(retries={"max_attempts": 3})
        
        # Verify client was called with the Config object
        args, kwargs = mock_session.client.call_args
        assert kwargs["config"] == mock_config


def test_configure_with_model_endpoint_as_endpoint_url(bedrock_adapter, connector_entity):
    """
    Test configuration using model_endpoint as endpoint_url.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    # Remove endpoint_url from client params to test model_endpoint usage
    connector_entity.params["client"] = {}
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        bedrock_adapter.configure(connector_entity)
        
        # Verify client was called with endpoint_url from model_endpoint
        args, kwargs = mock_session.client.call_args
        assert kwargs["endpoint_url"] == "https://bedrock-runtime.us-east-1.amazonaws.com"


def test_configure_ignores_short_model_endpoint(bedrock_adapter, connector_entity):
    """
    Test configuration ignores placeholder model_endpoint.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    connector_entity.model_endpoint = "DEFAULT"
    connector_entity.params["client"] = {}
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.logger') as mock_logger:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        bedrock_adapter.configure(connector_entity)
        
        # Verify logger was called about ignoring placeholder
        mock_logger.info.assert_called_once()
        assert "Ignoring placeholder" in mock_logger.info.call_args.args[0]
        assert "DEFAULT" in mock_logger.info.call_args.args[1]
        
        # Verify endpoint_url was not set
        args, kwargs = mock_session.client.call_args
        assert "endpoint_url" not in kwargs


def test_configure_client_endpoint_url_overrides_model_endpoint(bedrock_adapter, connector_entity):
    """
    Test that client.endpoint_url overrides model_endpoint.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    connector_entity.params["client"]["endpoint_url"] = "https://custom-endpoint.com"
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.logger') as mock_logger:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        bedrock_adapter.configure(connector_entity)
        
        # Verify logger was called about override
        mock_logger.info.assert_called_once()
        assert "override" in mock_logger.info.call_args.args[0]
        
        # Verify client was called with the override endpoint_url
        args, kwargs = mock_session.client.call_args
        assert kwargs["endpoint_url"] == "https://custom-endpoint.com"


def test_configure_minimal_params(bedrock_adapter):
    """
    Test configuration with minimal params.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
    """
    minimal_entity = ConnectorEntity(
        connector_adapter="aws_bedrock",
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        model_endpoint="",
        params={},
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt=""
    )
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        bedrock_adapter.configure(minimal_entity)
        
        # Verify session was created with empty kwargs
        mock_session_class.assert_called_once_with()
        
        # Verify client was created with minimal params
        args, kwargs = mock_session.client.call_args
        assert args[0] == "bedrock-runtime"
        assert len(kwargs) == 0  # No additional kwargs


# ================================
# Test get_response
# ================================
@pytest.mark.asyncio
async def test_get_response_success_single_text_content(bedrock_adapter, connector_entity):
    """
    Test successful response with single text content.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    mock_response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {"text": "This is a test response"}
                ]
            }
        }
    }
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = mock_response
        
        bedrock_adapter.configure(connector_entity)
        result = await bedrock_adapter.get_response("Test prompt")
        
        assert result.response == "This is a test response"
        
        # Verify the call to converse
        mock_to_thread.assert_called_once()
        lambda_func = mock_to_thread.call_args.args[0]
        # Execute the lambda to verify it calls converse correctly
        lambda_func()
        mock_client.converse.assert_called_once()


@pytest.mark.asyncio
async def test_get_response_success_multiple_text_content(bedrock_adapter, connector_entity):
    """
    Test successful response with multiple text content pieces.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    mock_response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {"text": "First part"},
                    {"text": "Second part"},
                    {"image": "ignored_content"},  # Should be ignored
                    {"text": "Third part"}
                ]
            }
        }
    }
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = mock_response
        
        bedrock_adapter.configure(connector_entity)
        result = await bedrock_adapter.get_response("Test prompt")
        
        assert result.response == "First part\n\nSecond part\n\nThird part"


@pytest.mark.asyncio
async def test_get_response_with_prompts_and_params(bedrock_adapter, connector_entity):
    """
    Test response with pre/post prompts and inference config.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    connector_entity.connector_pre_prompt = "Pre: "
    connector_entity.connector_post_prompt = " :Post"
    
    mock_response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Response"}]
            }
        }
    }
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = mock_response
        
        bedrock_adapter.configure(connector_entity)
        result = await bedrock_adapter.get_response("Test")
        
        # Verify the lambda function parameters
        lambda_func = mock_to_thread.call_args.args[0]
        lambda_func()
        
        call_args = mock_client.converse.call_args
        assert call_args.kwargs["modelId"] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert call_args.kwargs["messages"][0]["content"][0]["text"] == "Pre: Test :Post"
        assert "inferenceConfig" in call_args.kwargs
        assert call_args.kwargs["inferenceConfig"]["temperature"] == 0.7


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", [
    {
        "name": "no_message",
        "response": {"output": {"message": None}},
        "error_contains": "assistant message with content"
    },
    {
        "name": "wrong_role",
        "response": {
            "output": {
                "message": {
                    "role": "user",
                    "content": [{"text": "Response"}]
                }
            }
        },
        "error_contains": "assistant message with content"
    },
    {
        "name": "empty_content",
        "response": {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": []
                }
            }
        },
        "error_contains": "assistant message with content"
    },
    {
        "name": "missing_output",
        "response": {"some_field": "value"},
        "error_contains": "'output'"
    },
    {
        "name": "missing_message_in_output",
        "response": {"output": {"some_field": "value"}},
        "error_contains": "'message'"
    }
])
async def test_get_response_error_cases(bedrock_adapter, connector_entity, test_case):
    """
    Test various error cases in get_response.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
        test_case: Parametrized test case data with response and expected error.
    """
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread, \
         patch('adapters.connector.aws_bedrock_adapter.logger') as mock_logger:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = test_case["response"]
        
        bedrock_adapter.configure(connector_entity)
        
        with pytest.raises(Exception) as exc_info:
            await bedrock_adapter.get_response("Test prompt")
        
        # Verify error logging
        mock_logger.error.assert_called_once()
        assert AWSBedrockAdapter.ERROR_PROCESSING_PROMPT in mock_logger.error.call_args.args[0]
        
        # Verify error contains expected text
        assert test_case["error_contains"] in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_response_boto3_exception(bedrock_adapter, connector_entity):
    """
    Test handling of boto3 exceptions.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread, \
         patch('adapters.connector.aws_bedrock_adapter.logger') as mock_logger:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        # Simulate boto3 exception
        boto3_error = Exception("AWS service error")
        mock_to_thread.side_effect = boto3_error
        
        bedrock_adapter.configure(connector_entity)
        
        with pytest.raises(Exception) as exc_info:
            await bedrock_adapter.get_response("Test prompt")
        
        assert str(exc_info.value) == "AWS service error"
        
        # Verify error logging
        mock_logger.error.assert_called_once()
        assert AWSBedrockAdapter.ERROR_PROCESSING_PROMPT in mock_logger.error.call_args.args[0]


@pytest.mark.asyncio
async def test_get_response_empty_prompt(bedrock_adapter, connector_entity):
    """
    Test response with empty prompt (should still work).
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    mock_response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Empty prompt response"}]
            }
        }
    }
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = mock_response
        
        bedrock_adapter.configure(connector_entity)
        result = await bedrock_adapter.get_response("")
        
        assert result.response == "Empty prompt response"


@pytest.mark.asyncio
async def test_get_response_none_prompt(bedrock_adapter, connector_entity):
    """
    Test response with None prompt (should still work).
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    mock_response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "None prompt response"}]
            }
        }
    }
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = mock_response
        
        bedrock_adapter.configure(connector_entity)
        result = await bedrock_adapter.get_response(None)
        
        assert result.response == "None prompt response"


@pytest.mark.asyncio
async def test_get_response_with_guardrail_config(bedrock_adapter, connector_entity):
    """
    Test response with guardrail configuration.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    connector_entity.params["guardrailConfig"] = {
        "guardrailIdentifier": "test-guardrail",
        "guardrailVersion": "1"
    }
    
    mock_response = {
        "output": {
            "message": {
                "role": "assistant", 
                "content": [{"text": "Guardrail response"}]
            }
        }
    }
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = mock_response
        
        bedrock_adapter.configure(connector_entity)
        await bedrock_adapter.get_response("Test")
        
        # Verify guardrail config was passed
        lambda_func = mock_to_thread.call_args.args[0]
        lambda_func()
        
        call_args = mock_client.converse.call_args
        assert "guardrailConfig" in call_args.kwargs
        assert call_args.kwargs["guardrailConfig"]["guardrailIdentifier"] == "test-guardrail"


@pytest.mark.asyncio 
async def test_get_response_no_text_content(bedrock_adapter, connector_entity):
    """
    Test response processing when no text content is available.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    mock_response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {"image": "base64_data"},
                    {"video": "video_data"}
                ]
            }
        }
    }
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = mock_response
        
        bedrock_adapter.configure(connector_entity)
        result = await bedrock_adapter.get_response("Test")
        
        # Should return empty string when no text content is found
        assert result.response == ""


@pytest.mark.asyncio
async def test_get_response_numeric_prompt(bedrock_adapter, connector_entity):
    """
    Test response with numeric prompt.
    
    Args:
        bedrock_adapter: AWS Bedrock adapter fixture.
        connector_entity: Test connector entity fixture.
    """
    mock_response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Numeric response"}]
            }
        }
    }
    
    with patch('adapters.connector.aws_bedrock_adapter.boto3.Session') as mock_session_class, \
         patch('adapters.connector.aws_bedrock_adapter.asyncio.to_thread') as mock_to_thread:
        
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_to_thread.return_value = mock_response
        
        bedrock_adapter.configure(connector_entity)
        result = await bedrock_adapter.get_response(12345)
        
        assert result.response == "Numeric response"
        
        # Verify the prompt was converted to string in the message
        lambda_func = mock_to_thread.call_args.args[0]
        lambda_func()
        
        call_args = mock_client.converse.call_args
        assert call_args.kwargs["messages"][0]["content"][0]["text"] == "12345"