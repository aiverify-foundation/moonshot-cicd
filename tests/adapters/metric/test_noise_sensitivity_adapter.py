import pytest
from pathlib import Path

from adapters.metric.noise_sensitivity_adapter import NoiseSensitivityAdapter
from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.connector_entity import ConnectorEntity


@pytest.fixture
def mock_connector_entity():
    """
    Create a mock connector entity.
    
    Returns:
        ConnectorEntity: A test connector entity with OpenAI configuration.
    """
    return ConnectorEntity(
        model="gpt-4",
        connector_adapter="openai",
        api_key="test-key"
    )


@pytest.fixture
def mock_metric_config(mock_connector_entity):
    """
    Create a mock metric configuration entity.
    
    Args:
        mock_connector_entity: Fixture providing a mock connector entity.
        
    Returns:
        MetricConfigEntity: A test metric configuration entity.
    """
    return MetricConfigEntity(
        name="noise_sensitivity",
        connector_configurations=mock_connector_entity,
        params={}
    )


@pytest.fixture
def metric_individual_entity():
    """
    Create a test metric individual entity.
    
    Returns:
        MetricIndividualEntity: A test metric individual entity with sample data.
    """
    predicted_result = ConnectorResponseEntity(
        response="This is a test response",
        context=["Context 1", "Context 2"]
    )
    
    return MetricIndividualEntity(
        prompt="What is the answer?",
        predicted_result=predicted_result,
        target="Expected answer",
        reference_context="Reference context for evaluation",
        evaluated_result={}
    )


@pytest.fixture
def metric_individual_entities():
    """
    Create a list of test metric individual entities.
    
    Returns:
        list: A list of MetricIndividualEntity objects with varying scores.
    """
    entities = []
    for i in range(3):
        predicted_result = ConnectorResponseEntity(
            response=f"Response {i}",
            context=[f"Context {i}A", f"Context {i}B"]
        )
        entity = MetricIndividualEntity(
            prompt=f"Prompt {i}",
            predicted_result=predicted_result,
            target=f"Target {i}",
            reference_context=f"Reference {i}",
            evaluated_result={"score": 0.8 + (i * 0.1)}  # Scores: 0.8, 0.9, 1.0
        )
        entities.append(entity)
    return entities


# ================================
# Test __init__
# ================================
def test_init_success(mocker):
    """
    Test successful initialization of NoiseSensitivityAdapter.
    """
    mock_path = mocker.patch('adapters.metric.noise_sensitivity_adapter.Path')
    mock_logger = mocker.patch('adapters.metric.noise_sensitivity_adapter.logger')
    mock_path.return_value.stem = "noise_sensitivity"
    mock_connector = mocker.MagicMock()
    
    mocker.patch.object(NoiseSensitivityAdapter, 'get_metric_config', return_value=mocker.MagicMock())
    mocker.patch.object(NoiseSensitivityAdapter, 'get_metric_connectors', return_value={"metric": mock_connector})
    
    adapter = NoiseSensitivityAdapter()
    
    assert adapter.metric_connectors == {"metric": mock_connector}
    assert adapter.selected_metric_connector == mock_connector


def test_init_with_no_config(mocker):
    """
    Test initialization when no metric config is found.
    """
    mock_path = mocker.patch('adapters.metric.noise_sensitivity_adapter.Path')
    mock_logger = mocker.patch('adapters.metric.noise_sensitivity_adapter.logger')
    mock_path.return_value.stem = "noise_sensitivity"
    
    mocker.patch.object(NoiseSensitivityAdapter, 'get_metric_config', return_value=None)
    
    adapter = NoiseSensitivityAdapter()
    assert not hasattr(adapter, 'metric_connectors')
    assert not hasattr(adapter, 'selected_metric_connector')


def test_init_with_no_connectors(mocker, mock_metric_config):
    """
    Test initialization when no metric connectors are found.
    """
    mock_path = mocker.patch('adapters.metric.noise_sensitivity_adapter.Path')
    mock_logger = mocker.patch('adapters.metric.noise_sensitivity_adapter.logger')
    mock_path.return_value.stem = "noise_sensitivity"
    
    mocker.patch.object(NoiseSensitivityAdapter, 'get_metric_config', return_value=mock_metric_config)
    mocker.patch.object(NoiseSensitivityAdapter, 'get_metric_connectors', return_value=None)
    
    adapter = NoiseSensitivityAdapter()
    assert adapter.metric_config == mock_metric_config
    assert not hasattr(adapter, 'selected_metric_connector')


def test_init_exception_handling(mocker):
    """
    Test initialization exception handling.
    """
    mock_path = mocker.patch('adapters.metric.noise_sensitivity_adapter.Path')
    mock_logger = mocker.patch('adapters.metric.noise_sensitivity_adapter.logger')
    mock_path.return_value.stem = "noise_sensitivity"
    
    mocker.patch.object(NoiseSensitivityAdapter, 'get_metric_config', side_effect=Exception("Config error"))
    
    with pytest.raises(Exception):
        NoiseSensitivityAdapter()
    
    mock_logger.error.assert_called_once()


# ================================
# Test get_metric_connectors
# ================================
def test_get_metric_connectors_success(mocker, mock_metric_config):
    """
    Test successful retrieval of metric connectors.
    """
    mock_module_loader = mocker.patch('adapters.metric.noise_sensitivity_adapter.ModuleLoader')
    mock_logger = mocker.patch('adapters.metric.noise_sensitivity_adapter.logger')
    mock_connector = mocker.MagicMock()
    mock_module_loader.load.return_value = (mock_connector, None)
    
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    result = adapter.get_metric_connectors(mock_metric_config)
    
    assert result == {"metric": mock_connector}
    mock_connector.configure.assert_called_once_with(mock_metric_config.connector_configurations)
    mock_logger.info.assert_called()


def test_get_metric_connectors_no_adapter(mocker, mock_metric_config):
    """
    Test get_metric_connectors when no connector adapter is specified.
    """
    mock_module_loader = mocker.patch('adapters.metric.noise_sensitivity_adapter.ModuleLoader')
    mock_logger = mocker.patch('adapters.metric.noise_sensitivity_adapter.logger')
    mock_metric_config.connector_configurations.connector_adapter = None
    
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    result = adapter.get_metric_connectors(mock_metric_config)
    
    assert result is None
    mock_module_loader.load.assert_not_called()


def test_get_metric_connectors_exception(mocker, mock_metric_config):
    """
    Test exception handling in get_metric_connectors.
    """
    mock_module_loader = mocker.patch('adapters.metric.noise_sensitivity_adapter.ModuleLoader')
    mock_logger = mocker.patch('adapters.metric.noise_sensitivity_adapter.logger')
    mock_module_loader.load.side_effect = Exception("Module error")
    
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    
    with pytest.raises(Exception):
        adapter.get_metric_connectors(mock_metric_config)
    
    mock_logger.error.assert_called_once()


# ================================
# Test update_metric_params
# ================================
@pytest.mark.parametrize("params,expected_behavior", [
    ({"threshold": 0.8, "temperature": 0.5}, "params_set"),
    ({}, "params_not_set"),
    (None, "params_not_set"),
])
def test_update_metric_params(params, expected_behavior):
    """
    Test updating metric parameters with different scenarios.
    """
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    
    adapter.update_metric_params(params)
    
    if expected_behavior == "params_set" and params:
        assert hasattr(adapter, 'params')
        assert adapter.params == params
    else:
        assert not hasattr(adapter, 'params')


# ================================
# Test get_individual_result
# ================================
@pytest.mark.asyncio
async def test_get_individual_result_success(mocker, metric_individual_entity):
    """
    Test successful evaluation of individual result.
    """
    # Setup mocks
    mock_noise_sensitivity = mocker.patch('adapters.metric.noise_sensitivity_adapter.NoiseSensitivity')
    mock_llm_wrapper = mocker.patch('adapters.metric.noise_sensitivity_adapter.LangchainLLMWrapper')
    mock_sample = mocker.patch('adapters.metric.noise_sensitivity_adapter.SingleTurnSample')
    
    mock_connector = mocker.MagicMock()
    mock_llm_client = mocker.MagicMock()
    mock_connector.get_client.return_value = mock_llm_client
    mock_evaluator_llm = mocker.MagicMock()
    mock_llm_wrapper.return_value = mock_evaluator_llm
    mock_sample_instance = mocker.MagicMock()
    mock_sample.return_value = mock_sample_instance
    mock_scorer = mocker.MagicMock()
    mock_noise_sensitivity.return_value = mock_scorer
    mock_scorer.single_turn_ascore = mocker.AsyncMock(return_value=0.85)
    
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    adapter.selected_metric_connector = mock_connector
    
    result = await adapter.get_individual_result(metric_individual_entity)
    
    expected_result = {
        "prompt": "What is the answer?",
        "predicted_value": "This is a test response",
        "reference_context": "Reference context for evaluation",
        "context": ["Context 1", "Context 2"],
        "target": "Expected answer",
        "score": 0.85,
    }
    
    assert result == expected_result
    mock_connector.get_client.assert_called_once()
    mock_llm_wrapper.assert_called_once_with(mock_llm_client)
    mock_sample.assert_called_once_with(
        user_input="What is the answer?",
        response="This is a test response",
        reference="Reference context for evaluation",
        retrieved_contexts=["Context 1", "Context 2"]
    )
    mock_noise_sensitivity.assert_called_once_with(llm=mock_evaluator_llm)
    mock_scorer.single_turn_ascore.assert_called_once_with(mock_sample_instance)


@pytest.mark.asyncio
async def test_get_individual_result_no_connector(mocker):
    """
    Test get_individual_result when no connector is available.
    """
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    adapter.selected_metric_connector = None
    
    with pytest.raises(RuntimeError, match="No metric connector available for evaluation"):
        await adapter.get_individual_result(mocker.MagicMock())

# ================================
# Test get_results
# ================================
@pytest.mark.asyncio
async def test_get_results_success(metric_individual_entities):
    """
    Test successful aggregation of results.
    """
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    
    result = await adapter.get_results(metric_individual_entities)
    
    # Expected average: (0.8 + 0.9 + 1.0) / 3 = 0.9
    expected_result = {
        "noise_sensitivity": {
            "average_score": 0.9,
        },
    }
    
    assert result == expected_result


@pytest.mark.asyncio
async def test_get_results_empty_entities():
    """
    Test get_results with empty entity list.
    """
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    
    with pytest.raises(ZeroDivisionError):
        await adapter.get_results([])


@pytest.mark.asyncio
async def test_get_results_entities_without_scores():
    """
    Test get_results with entities that have no score in evaluated_result.
    """
    entities = []
    for i in range(2):
        predicted_result = ConnectorResponseEntity(response=f"Response {i}")
        entity = MetricIndividualEntity(
            prompt=f"Prompt {i}",
            predicted_result=predicted_result,
            target=f"Target {i}",
            evaluated_result={}  # No score
        )
        entities.append(entity)
    
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    
    result = await adapter.get_results(entities)
    
    # Should default to 0 for missing scores
    expected_result = {
        "noise_sensitivity": {
            "average_score": 0.0,
        },
    }
    
    assert result == expected_result


@pytest.mark.asyncio
async def test_get_results_exception(mocker, metric_individual_entities):
    """
    Test exception handling in get_results.
    """
    mock_logger = mocker.patch('adapters.metric.noise_sensitivity_adapter.logger')
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    
    # Force an exception by making entities non-iterable
    mocker.patch('builtins.sum', side_effect=Exception("Sum error"))
    
    with pytest.raises(Exception):
        await adapter.get_results(metric_individual_entities)
    
    mock_logger.error.assert_called_once()


# ================================
# Integration Tests
# ================================
@pytest.mark.asyncio
async def test_full_workflow_integration(mocker, mock_metric_config, metric_individual_entity):
    """
    Test the full workflow from initialization to getting individual results.
    """
    # Setup mocks for initialization
    mock_path = mocker.patch('adapters.metric.noise_sensitivity_adapter.Path')
    mock_module_loader = mocker.patch('adapters.metric.noise_sensitivity_adapter.ModuleLoader')
    mock_noise_sensitivity = mocker.patch('adapters.metric.noise_sensitivity_adapter.NoiseSensitivity')
    mock_llm_wrapper = mocker.patch('adapters.metric.noise_sensitivity_adapter.LangchainLLMWrapper')
    mock_sample = mocker.patch('adapters.metric.noise_sensitivity_adapter.SingleTurnSample')
    
    mock_path.return_value.stem = "noise_sensitivity"
    mock_connector = mocker.MagicMock()
    mock_module_loader.load.return_value = (mock_connector, None)
    
    # Setup mocks for evaluation
    mock_llm_client = mocker.MagicMock()
    mock_connector.get_client.return_value = mock_llm_client
    mock_evaluator_llm = mocker.MagicMock()
    mock_llm_wrapper.return_value = mock_evaluator_llm
    mock_sample_instance = mocker.MagicMock()
    mock_sample.return_value = mock_sample_instance
    mock_scorer = mocker.MagicMock()
    mock_noise_sensitivity.return_value = mock_scorer
    mock_scorer.single_turn_ascore = mocker.AsyncMock(return_value=0.75)
    
    mocker.patch.object(NoiseSensitivityAdapter, 'get_metric_config', return_value=mock_metric_config)
    
    adapter = NoiseSensitivityAdapter()
    
    # Test parameter update
    adapter.update_metric_params({"test_param": "test_value"})
    assert adapter.params == {"test_param": "test_value"}
    
    # Test individual result evaluation
    result = await adapter.get_individual_result(metric_individual_entity)
    
    assert result["score"] == 0.75
    assert result["prompt"] == "What is the answer?"
    assert result["predicted_value"] == "This is a test response"
    
    # Test aggregated results
    metric_individual_entity.evaluated_result = result
    entities = [metric_individual_entity]
    aggregated_result = await adapter.get_results(entities)
    
    assert aggregated_result["noise_sensitivity"]["average_score"] == 0.75


@pytest.mark.parametrize("score_values,expected_average", [
    ([0.1, 0.2, 0.3], 0.2),
    ([1.0, 1.0, 1.0], 1.0),
    ([0.0, 0.5, 1.0], 0.5),
    ([0.95, 0.85, 0.75], 0.85),
])
@pytest.mark.asyncio
async def test_get_results_various_score_scenarios(score_values, expected_average):
    """
    Test get_results with various score scenarios using parametrize.
    """
    entities = []
    for i, score in enumerate(score_values):
        predicted_result = ConnectorResponseEntity(response=f"Response {i}")
        entity = MetricIndividualEntity(
            prompt=f"Prompt {i}",
            predicted_result=predicted_result,
            target=f"Target {i}",
            evaluated_result={"score": score}
        )
        entities.append(entity)
    
    adapter = NoiseSensitivityAdapter.__new__(NoiseSensitivityAdapter)
    result = await adapter.get_results(entities)
    
    assert result["noise_sensitivity"]["average_score"] == pytest.approx(expected_average)
