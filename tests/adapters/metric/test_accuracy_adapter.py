import pytest
from pathlib import Path
from adapters.metric.accuracy_adapter import AccuracyAdapter
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity


@pytest.fixture
def metric_individual_entity():
    """
    Create a test metric individual entity.
    
    Returns:
        MetricIndividualEntity: A test metric individual entity with sample data.
    """
    predicted_result = ConnectorResponseEntity(response="Expected answer")
    
    return MetricIndividualEntity(
        prompt="What is 2+2?",
        predicted_result=predicted_result,
        target="Expected answer",
        evaluated_result={}
    )

# ================================
# Test __init__
# ================================
def test_init_success(mocker):
    """
    Test successful initialization of AccuracyAdapter.
    """
    mock_config = mocker.MagicMock()
    mock_connector = mocker.MagicMock()
    
    def mock_get_metric_config(self, metric_id):
        return mock_config
    
    def mock_get_metric_connectors(self, config):
        return {"metric": mock_connector}
    
    mocker.patch("pathlib.Path.stem", "accuracy")
    mocker.patch.object(AccuracyAdapter, 'get_metric_config', mock_get_metric_config)
    mocker.patch.object(AccuracyAdapter, 'get_metric_connectors', mock_get_metric_connectors)
    
    adapter = AccuracyAdapter()
    
    assert adapter.metric_config == mock_config
    assert adapter.metric_connectors == {"metric": mock_connector}
    assert adapter.selected_metric_connector == mock_connector

def test_init_exception_handling(mocker):
    """
    Test initialization exception handling.
    """
    mock_logger = mocker.MagicMock()
    
    def mock_get_metric_config(self, metric_id):
        raise Exception("Config error")
    
    mocker.patch("pathlib.Path.stem", "accuracy")
    mocker.patch.object(AccuracyAdapter, 'get_metric_config', mock_get_metric_config)
    mocker.patch('adapters.metric.accuracy_adapter.logger', mock_logger)
    
    with pytest.raises(Exception):
        AccuracyAdapter()
    
    mock_logger.error.assert_called_once()

# ================================
# Test get_metric_connectors
# ================================
def test_get_metric_connectors_success(mocker):
    """
    Test successful retrieval of metric connectors.
    """
    mock_config = mocker.MagicMock()
    mock_config.connector_configurations.model = "gpt-4"
    mock_config.connector_configurations.connector_adapter = "openai"
    mock_connector = mocker.MagicMock()
    mock_module_loader = mocker.MagicMock()
    
    mock_module_loader.load.return_value = mock_connector
    mocker.patch('adapters.metric.accuracy_adapter.ModuleLoader', mock_module_loader)
    
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    result = adapter.get_metric_connectors(mock_config)
    
    assert result == {"metric": mock_connector}
    mock_connector.configure.assert_called_once()

def test_get_metric_connectors_exception(mocker):
    """
    Test exception handling in get_metric_connectors.
    """
    mock_config = mocker.MagicMock()
    mock_config.connector_configurations.connector_adapter = "openai"
    mock_module_loader = mocker.MagicMock()
    mock_logger = mocker.MagicMock()
    
    mock_module_loader.load.side_effect = Exception("Module error")
    mocker.patch('adapters.metric.accuracy_adapter.ModuleLoader', mock_module_loader)
    mocker.patch('adapters.metric.accuracy_adapter.logger', mock_logger)
    
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    
    with pytest.raises(Exception):
        adapter.get_metric_connectors(mock_config)
    
    mock_logger.error.assert_called_once()

# ================================
# Test update_metric_params
# ================================
def test_update_metric_params():
    """
    Test updating metric parameters.
    """
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    test_params = {"threshold": 0.8}
    
    adapter.update_metric_params(test_params)
    
    assert adapter.params == test_params

def test_update_metric_params_empty():
    """
    Test updating with empty parameters.
    """
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    
    adapter.update_metric_params({})
    
    assert not hasattr(adapter, 'params')

# ================================
# Test get_individual_result
# ================================
@pytest.mark.asyncio
async def test_get_individual_result_accurate(metric_individual_entity):
    """
    Test get_individual_result when prediction matches target.
    """
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    
    result = await adapter.get_individual_result(metric_individual_entity)
    
    expected_result = {
        "prompt": "What is 2+2?",
        "predicted_value": "Expected answer",
        "target": "Expected answer",
        "accuracy": True
    }
    
    assert result == expected_result

@pytest.mark.asyncio
async def test_get_individual_result_inaccurate(metric_individual_entity):
    """
    Test get_individual_result when prediction doesn't match target.
    """
    metric_individual_entity.predicted_result.response = "Wrong answer"
    
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    
    result = await adapter.get_individual_result(metric_individual_entity)
    
    assert result["accuracy"] is False
    assert result["predicted_value"] == "Wrong answer"

@pytest.mark.asyncio
async def test_get_individual_result_exception(mocker):
    """
    Test exception handling in get_individual_result.
    """
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    mock_logger = mocker.MagicMock()
    
    mocker.patch('adapters.metric.accuracy_adapter.logger', mock_logger)
    
    with pytest.raises(AttributeError):
        await adapter.get_individual_result(None)
    
    mock_logger.error.assert_called_once()

# ================================
# Test get_results
# ================================
@pytest.mark.asyncio
async def test_get_results_full_accuracy():
    """
    Test get_results with 100% accuracy.
    """
    entities = []
    for i in range(3):
        entity = MetricIndividualEntity(
            prompt=f"Prompt {i}",
            predicted_result=ConnectorResponseEntity(response=f"Answer {i}"),
            target=f"Answer {i}",
            evaluated_result={"accuracy": True}
        )
        entities.append(entity)
    
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    
    result = await adapter.get_results(entities)
    
    assert result["accuracy"]["exact_string_match"] == 100.0

@pytest.mark.asyncio
async def test_get_results_partial_accuracy():
    """
    Test get_results with partial accuracy.
    """
    entities = [
        MetricIndividualEntity(
            prompt="Prompt 1",
            predicted_result=ConnectorResponseEntity(response="Correct"),
            target="Correct",
            evaluated_result={"accuracy": True}
        ),
        MetricIndividualEntity(
            prompt="Prompt 2",
            predicted_result=ConnectorResponseEntity(response="Wrong"),
            target="Correct",
            evaluated_result={"accuracy": False}
        )
    ]
    
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    
    result = await adapter.get_results(entities)
    
    assert result["accuracy"]["exact_string_match"] == 50.0

@pytest.mark.asyncio
async def test_get_results_exception(mocker):
    """
    Test exception handling in get_results.
    """
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    mock_logger = mocker.MagicMock()
    
    mocker.patch('adapters.metric.accuracy_adapter.logger', mock_logger)
    
    with pytest.raises(ZeroDivisionError):
        await adapter.get_results([])
    
    mock_logger.error.assert_called_once()