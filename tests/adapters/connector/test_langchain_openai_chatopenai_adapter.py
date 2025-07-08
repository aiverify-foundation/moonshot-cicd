import os
import pytest
from unittest.mock import patch, Mock, MagicMock
from adapters.connector.langchain_openai_chatopenai_adapter import LangchainOpenAIChatOpenAIAdapter
from domain.entities.connector_entity import ConnectorEntity


@pytest.fixture
def connector_entity():
    """
    Create a test connector entity for Langchain OpenAI ChatOpenAI.
    
    Returns:
        ConnectorEntity: A test connector entity with Langchain OpenAI ChatOpenAI configuration.
    """
    return ConnectorEntity(
        connector_adapter="langchain_openai_chatopenai",
        model="gpt-4",
        model_endpoint="https://api.openai.com/v1",
        params={},
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt=""
    )

@pytest.fixture
def langchain_adapter():
    """
    Create a Langchain OpenAI ChatOpenAI adapter instance.
    
    Returns:
        LangchainOpenAIChatOpenAIAdapter: A fresh Langchain OpenAI ChatOpenAI adapter instance for testing.
    """
    return LangchainOpenAIChatOpenAIAdapter()

# ================================
# Test configure
# ================================
def test_configure_with_api_key_model_and_endpoint(langchain_adapter, connector_entity):
    """
    Test successful configuration with API key, model, and custom endpoint.
    
    Args:
        langchain_adapter: Langchain OpenAI ChatOpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.langchain_openai_chatopenai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.langchain_openai_chatopenai_adapter.ChatOpenAI') as mock_chatopenai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_chatopenai_class.return_value = mock_client
        
        langchain_adapter.configure(connector_entity)
        
        assert langchain_adapter.connector_entity == connector_entity
        assert langchain_adapter._client == mock_client
        
        # Verify ChatOpenAI was called with correct parameters
        mock_chatopenai_class.assert_called_once_with(
            api_key="test-api-key",
            model="gpt-4",
            base_url="https://api.openai.com/v1"
        )

def test_configure_with_empty_api_key(langchain_adapter, connector_entity):
    """
    Test configuration with empty/None API key.
    
    Args:
        langchain_adapter: Langchain OpenAI ChatOpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.langchain_openai_chatopenai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.langchain_openai_chatopenai_adapter.ChatOpenAI') as mock_chatopenai_class:
        
        mock_getenv.return_value = None
        mock_client = MagicMock()
        mock_chatopenai_class.return_value = mock_client
        
        langchain_adapter.configure(connector_entity)
        
        # Verify ChatOpenAI was called with empty string for api_key
        mock_chatopenai_class.assert_called_once_with(
            api_key="",
            model="gpt-4",
            base_url="https://api.openai.com/v1"
        )

def test_configure_minimal_setup(langchain_adapter):
    """
    Test configuration with minimal connector entity.
    
    Args:
        langchain_adapter: Langchain OpenAI ChatOpenAI adapter fixture.
    """
    minimal_entity = ConnectorEntity(
        connector_adapter="langchain_openai_chatopenai",
        model="",
        model_endpoint="",
        params={},
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt=""
    )
    
    with patch('adapters.connector.langchain_openai_chatopenai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.langchain_openai_chatopenai_adapter.ChatOpenAI') as mock_chatopenai_class:
        
        mock_getenv.return_value = None
        mock_client = MagicMock()
        mock_chatopenai_class.return_value = mock_client
        
        langchain_adapter.configure(minimal_entity)
        
        # Verify ChatOpenAI was called with minimal parameters
        mock_chatopenai_class.assert_called_once_with(
            api_key="",
            model=None,
            base_url=None
        )

# ================================
# Test get_client
# ================================
def test_get_client_returns_configured_client(langchain_adapter, connector_entity):
    """
    Test that get_client returns the configured ChatOpenAI client.
    
    Args:
        langchain_adapter: Langchain OpenAI ChatOpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.langchain_openai_chatopenai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.langchain_openai_chatopenai_adapter.ChatOpenAI') as mock_chatopenai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_chatopenai_class.return_value = mock_client
        
        # Configure the adapter first
        langchain_adapter.configure(connector_entity)
        
        # Get the client
        returned_client = langchain_adapter.get_client()
        
        # Verify it returns the same client instance
        assert returned_client == mock_client
        assert returned_client == langchain_adapter._client

def test_get_client_before_configure(langchain_adapter):
    """
    Test get_client behavior before configure is called.
    
    Args:
        langchain_adapter: Langchain OpenAI ChatOpenAI adapter fixture.
    """
    # This should raise AttributeError since _client hasn't been set
    with pytest.raises(AttributeError):
        langchain_adapter.get_client()

# ================================
# Test get_response
# ================================
@pytest.mark.asyncio
async def test_get_response_raises_not_implemented_error(langchain_adapter, connector_entity):
    """
    Test that get_response raises NotImplementedError.
    
    Args:
        langchain_adapter: Langchain OpenAI ChatOpenAI adapter fixture.
        connector_entity: Connector entity fixture with test configuration.
    """
    with patch('adapters.connector.langchain_openai_chatopenai_adapter.os.getenv') as mock_getenv, \
         patch('adapters.connector.langchain_openai_chatopenai_adapter.ChatOpenAI') as mock_chatopenai_class:
        
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_chatopenai_class.return_value = mock_client
        
        langchain_adapter.configure(connector_entity)
        
        with pytest.raises(NotImplementedError) as exc_info:
            await langchain_adapter.get_response("Test prompt")
        
        # Verify the specific error message
        assert str(exc_info.value) == "This connector is not supposed to generate response."

@pytest.mark.asyncio
async def test_get_response_before_configure(langchain_adapter):
    """
    Test get_response behavior before configure is called.
    
    Args:
        langchain_adapter: Langchain OpenAI ChatOpenAI adapter fixture.
    """
    # Should still raise NotImplementedError, not AttributeError
    with pytest.raises(NotImplementedError) as exc_info:
        await langchain_adapter.get_response("Test prompt")
    
    assert str(exc_info.value) == "This connector is not supposed to generate response."