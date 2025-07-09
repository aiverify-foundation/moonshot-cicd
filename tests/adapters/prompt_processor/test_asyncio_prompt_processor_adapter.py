import asyncio
import pytest
from unittest.mock import AsyncMock, patch, Mock, MagicMock

from adapters.prompt_processor.asyncio_prompt_processor_adapter import AsyncioPromptProcessor
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.prompt_entity import PromptEntity
from domain.ports.connector_port import ConnectorPort
from domain.ports.metric_port import MetricPort
from domain.services.enums.task_manager_status import TaskManagerStatus


@pytest.fixture
def asyncio_processor():
    """
    Create an AsyncioPromptProcessor instance.
    
    Returns:
        AsyncioPromptProcessor: An instance with mocked AppConfig.
    """
    with patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.AppConfig'):
        return AsyncioPromptProcessor()


@pytest.fixture
def prompt_entity():
    """
    Create a test prompt entity.
    
    Returns:
        PromptEntity: A test prompt entity with sample data.
    """
    return PromptEntity(
        index=0,
        prompt="Test prompt",
        target="Expected response",
        reference_context="Test context"
    )


@pytest.fixture
def connector_entity():
    """
    Create a test connector entity.
    
    Returns:
        ConnectorEntity: A test connector entity with OpenAI configuration.
    """
    return ConnectorEntity(
        connector_adapter="openai",
        model="gpt-4",
        model_endpoint="https://api.openai.com/v1",
        params={
            "temperature": 0.7,
            "max_tokens": 1000,
            "max_concurrency": 5
        },
        connector_pre_prompt="",
        connector_post_prompt="",
        system_prompt="You are a helpful assistant."
    )


@pytest.fixture
def metric_config():
    """
    Create a test metric configuration.
    
    Returns:
        dict: A metric configuration dictionary with accuracy settings.
    """
    return {
        "name": "accuracy",
        "params": {
            "threshold": 0.8
        }
    }


@pytest.fixture
def mock_connector_instance():
    """
    Create a mock connector instance.
    
    Returns:
        Mock: A mock connector instance implementing ConnectorPort.
    """
    mock = Mock(spec=ConnectorPort)
    mock.get_response = AsyncMock(return_value=ConnectorResponseEntity(response="Mock response", context=[]))
    return mock


@pytest.fixture
def mock_metric_instance():
    """
    Create a mock metric instance.
    
    Returns:
        Mock: A mock metric instance implementing MetricPort.
    """
    mock = Mock(spec=MetricPort)
    mock.get_individual_result = AsyncMock(return_value=0.9)
    mock.get_results = AsyncMock(return_value={"average_score": 0.85})
    mock.update_metric_params = Mock()
    return mock


# ================================
# Test __init__
# ================================
def test_init():
    """
    Test AsyncioPromptProcessor initialization.
    
    Verifies that the processor initializes correctly with AppConfig.
    """
    with patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.AppConfig') as mock_app_config:
        processor = AsyncioPromptProcessor()
        assert processor.app_config is not None
        mock_app_config.assert_called_once()


# ================================
# Test process_single_prompt
# ================================
@pytest.mark.asyncio
async def test_process_single_prompt_success(asyncio_processor, prompt_entity, mock_connector_instance, mock_metric_instance):
    """
    Test successful processing of a single prompt.
    
    Verifies that a prompt is processed successfully through the connector
    and metric evaluation pipeline.
    """
    # Setup
    mock_connector_instance.get_response.return_value = ConnectorResponseEntity(response="Mock response", context=[])
    mock_metric_instance.get_individual_result.return_value = 0.9
    
    # Execute
    result = await asyncio_processor.process_single_prompt(
        prompt_entity, mock_connector_instance, mock_metric_instance
    )
    
    # Verify
    assert result.model_prediction.response == "Mock response"
    assert result.state == TaskManagerStatus.COMPLETED
    assert result.evaluation_result is not None
    assert result.evaluation_result.evaluated_result == 0.9
    
    # Verify method calls
    mock_connector_instance.get_response.assert_called_once_with("Test prompt")
    mock_metric_instance.get_individual_result.assert_called_once()


@pytest.mark.asyncio
async def test_process_single_prompt_connector_error(asyncio_processor, prompt_entity, mock_connector_instance, mock_metric_instance):
    """
    Test error handling when connector fails.
    
    Verifies that connector errors are properly handled and prompt state
    is updated to ERROR.
    """
    # Setup
    mock_connector_instance.get_response.side_effect = Exception("Connector error")
    
    # Execute and verify
    with pytest.raises(Exception, match="Connector error"):
        await asyncio_processor.process_single_prompt(
            prompt_entity, mock_connector_instance, mock_metric_instance
        )
    
    assert prompt_entity.state == TaskManagerStatus.ERROR


@pytest.mark.asyncio
async def test_process_single_prompt_metric_error(asyncio_processor, prompt_entity, mock_connector_instance, mock_metric_instance):
    """
    Test error handling when metric evaluation fails.
    
    Verifies that metric errors are properly handled and prompt state
    is updated to ERROR.
    """
    # Setup
    mock_connector_instance.get_response.return_value = ConnectorResponseEntity(response="Mock response", context=[])
    mock_metric_instance.get_individual_result.side_effect = Exception("Metric error")
    
    # Execute and verify
    with pytest.raises(Exception, match="Metric error"):
        await asyncio_processor.process_single_prompt(
            prompt_entity, mock_connector_instance, mock_metric_instance
        )
    
    assert prompt_entity.state == TaskManagerStatus.ERROR


# ================================
# Test process_prompts
# ================================
@pytest.mark.asyncio
async def test_process_prompts_success(asyncio_processor, connector_entity, metric_config):
    """
    Test successful processing of multiple prompts.
    
    Verifies that multiple prompts are processed concurrently and
    evaluation summary is generated correctly.
    """
    # Setup prompts
    prompts = [
        PromptEntity(index=i, prompt=f"Test prompt {i}", target=f"Target {i}")
        for i in range(3)
    ]
    
    # Mock dependencies
    mock_connector_instance = Mock(spec=ConnectorPort)
    mock_connector_instance.get_response = AsyncMock(return_value=ConnectorResponseEntity(response="Mock response", context=[]))
    mock_connector_instance.configure = Mock()
    
    mock_metric_instance = Mock(spec=MetricPort)
    mock_metric_instance.get_individual_result = AsyncMock(return_value=0.9)
    mock_metric_instance.get_results = AsyncMock(return_value={"average_score": 0.85})
    mock_metric_instance.update_metric_params = Mock()
    
    mock_metric_config = Mock()
    mock_metric_config.params = {"threshold": 0.8}
    
    with patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.ModuleLoader.load') as mock_load, \
         patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.AppConfig') as mock_app_config_class:
        
        # Setup mock returns
        mock_load.side_effect = [
            (mock_connector_instance, "connector_id"),
            (mock_metric_instance, "metric_id")
        ]
        
        mock_app_config = Mock()
        mock_app_config.get_metric_config.return_value = mock_metric_config
        mock_app_config.get_common_config.return_value = 5
        mock_app_config_class.return_value = mock_app_config
        asyncio_processor.app_config = mock_app_config
        
        # Execute
        processed_prompts, evaluation_summary = await asyncio_processor.process_prompts(
            prompts, connector_entity, metric_config
        )
        
        # Verify
        assert len(processed_prompts) == 3
        assert all(prompt.state == TaskManagerStatus.COMPLETED for prompt in processed_prompts)
        assert all(prompt.model_prediction.response == "Mock response" for prompt in processed_prompts)
        assert evaluation_summary == {"average_score": 0.85}
        
        # Verify module loading
        assert mock_load.call_count == 2
        mock_connector_instance.configure.assert_called_once_with(connector_entity)
        mock_metric_instance.update_metric_params.assert_called_once_with({"threshold": 0.8})


@pytest.mark.asyncio
async def test_process_prompts_with_callback(asyncio_processor, connector_entity, metric_config):
    """
    Test processing prompts with callback function.
    
    Verifies that callback function is called during prompt processing
    to provide progress updates.
    """
    # Setup
    prompts = [PromptEntity(index=0, prompt="Test prompt", target="Target")]
    callback_calls = []
    
    def mock_callback(state, total, completed, index):
        callback_calls.append((state, total, completed, index))
    
    # Mock dependencies
    mock_connector_instance = Mock(spec=ConnectorPort)
    mock_connector_instance.get_response = AsyncMock(return_value=ConnectorResponseEntity(response="Mock response", context=[]))
    mock_connector_instance.configure = Mock()
    
    mock_metric_instance = Mock(spec=MetricPort)
    mock_metric_instance.get_individual_result = AsyncMock(return_value=0.9)
    mock_metric_instance.get_results = AsyncMock(return_value={"average_score": 0.85})
    mock_metric_instance.update_metric_params = Mock()
    
    mock_metric_config = Mock()
    mock_metric_config.params = {}
    
    with patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.ModuleLoader.load') as mock_load, \
         patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.AppConfig') as mock_app_config_class:
        
        mock_load.side_effect = [
            (mock_connector_instance, "connector_id"),
            (mock_metric_instance, "metric_id")
        ]
        
        mock_app_config = Mock()
        mock_app_config.get_metric_config.return_value = mock_metric_config
        mock_app_config.get_common_config.return_value = 5
        mock_app_config_class.return_value = mock_app_config
        asyncio_processor.app_config = mock_app_config
        
        # Execute
        await asyncio_processor.process_prompts(
            prompts, connector_entity, metric_config, callback_fn=mock_callback
        )
        
        # Verify callback was called
        assert len(callback_calls) >= 2  # At least running and completed states


@pytest.mark.asyncio
async def test_process_prompts_connector_loading_error(asyncio_processor, connector_entity, metric_config):
    """
    Test error handling when connector loading fails.
    
    Verifies that connector loading errors are properly raised.
    """
    prompts = [PromptEntity(index=0, prompt="Test prompt", target="Target")]
    
    with patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.ModuleLoader.load') as mock_load:
        mock_load.side_effect = Exception("Failed to load connector")
        
        with pytest.raises(Exception, match="Failed to load connector"):
            await asyncio_processor.process_prompts(prompts, connector_entity, metric_config)


@pytest.mark.asyncio
async def test_process_prompts_metric_loading_error(asyncio_processor, connector_entity, metric_config):
    """
    Test error handling when metric loading fails.
    
    Verifies that metric loading errors are properly raised.
    """
    prompts = [PromptEntity(index=0, prompt="Test prompt", target="Target")]
    
    mock_connector_instance = Mock(spec=ConnectorPort)
    mock_connector_instance.configure = Mock()
    
    with patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.ModuleLoader.load') as mock_load:
        mock_load.side_effect = [
            (mock_connector_instance, "connector_id"),
            Exception("Failed to load metric")
        ]
        
        with pytest.raises(Exception, match="Failed to load metric"):
            await asyncio_processor.process_prompts(prompts, connector_entity, metric_config)

@pytest.mark.asyncio
async def test_process_prompts_uses_default_max_concurrency(asyncio_processor, connector_entity, metric_config):
    """
    Test that default max_concurrency is used when not specified in params.
    
    Verifies that the processor falls back to default concurrency setting
    from AppConfig when not provided in connector params.
    """
    prompts = [PromptEntity(index=0, prompt="Test prompt", target="Target")]
    
    # Remove max_concurrency from params
    del connector_entity.params["max_concurrency"]
    
    mock_connector_instance = Mock(spec=ConnectorPort)
    mock_connector_instance.get_response = AsyncMock(return_value=ConnectorResponseEntity(response="Mock response", context=[]))
    mock_connector_instance.configure = Mock()
    
    mock_metric_instance = Mock(spec=MetricPort)
    mock_metric_instance.get_individual_result = AsyncMock(return_value=0.9)
    mock_metric_instance.get_results = AsyncMock(return_value={"average_score": 0.85})
    mock_metric_instance.update_metric_params = Mock()
    
    mock_metric_config = Mock()
    mock_metric_config.params = {}
    
    with patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.ModuleLoader.load') as mock_load, \
         patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.AppConfig') as mock_app_config_class:
        
        mock_load.side_effect = [
            (mock_connector_instance, "connector_id"),
            (mock_metric_instance, "metric_id")
        ]
        
        mock_app_config = Mock()
        mock_app_config.get_metric_config.return_value = mock_metric_config
        mock_app_config.get_common_config.return_value = 10  # Default value
        mock_app_config_class.return_value = mock_app_config
        asyncio_processor.app_config = mock_app_config
        
        # Execute
        await asyncio_processor.process_prompts(prompts, connector_entity, metric_config)
        
        # Verify default was requested
        mock_app_config.get_common_config.assert_called_with("max_concurrency")


@pytest.mark.asyncio
async def test_process_prompts_empty_list(asyncio_processor, connector_entity, metric_config):
    """
    Test processing an empty list of prompts.
    
    Verifies that processor handles empty prompt lists gracefully
    and returns appropriate empty results.
    """
    prompts = []
    
    mock_connector_instance = Mock(spec=ConnectorPort)
    mock_connector_instance.configure = Mock()
    
    mock_metric_instance = Mock(spec=MetricPort)
    mock_metric_instance.get_results = AsyncMock(return_value={"average_score": 0.0})
    mock_metric_instance.update_metric_params = Mock()
    
    mock_metric_config = Mock()
    mock_metric_config.params = {}
    
    with patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.ModuleLoader.load') as mock_load, \
         patch('adapters.prompt_processor.asyncio_prompt_processor_adapter.AppConfig') as mock_app_config_class:
        
        mock_load.side_effect = [
            (mock_connector_instance, "connector_id"),
            (mock_metric_instance, "metric_id")
        ]
        
        mock_app_config = Mock()
        mock_app_config.get_metric_config.return_value = mock_metric_config
        mock_app_config.get_common_config.return_value = 5
        mock_app_config_class.return_value = mock_app_config
        asyncio_processor.app_config = mock_app_config
        
        # Execute
        processed_prompts, evaluation_summary = await asyncio_processor.process_prompts(
            prompts, connector_entity, metric_config
        )
        
        # Verify
        assert len(processed_prompts) == 0
        assert evaluation_summary == {"average_score": 0.0}


# ================================
# Test class constants
# ================================
def test_class_constants():
    """
    Test that class constants are defined correctly.
    
    Verifies that all expected class constants are properly defined
    with correct string values.
    """
    assert AsyncioPromptProcessor.CONNECTOR_LOADED_MSG == "[AsyncioPromptProcessor] Connector module loaded successfully."
    assert AsyncioPromptProcessor.METRIC_LOADED_MSG == "[AsyncioPromptProcessor] Metric module loaded successfully."
    assert AsyncioPromptProcessor.ERROR_LOADING_CONNECTOR == "[AsyncioPromptProcessor] Failed to load the connector module."
    assert AsyncioPromptProcessor.ERROR_LOADING_METRIC == "[AsyncioPromptProcessor] Failed to load the metric module."
    assert AsyncioPromptProcessor.ERROR_PROCESSING_PROMPT == "[AsyncioPromptProcessor] Failed to process prompt."
