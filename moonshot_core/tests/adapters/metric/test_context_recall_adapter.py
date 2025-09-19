import pytest
from adapters.metric.context_recall_adapter import ContextRecallAdapter
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity


@pytest.fixture
def metric_individual_entity():
    """
    Create a test metric individual entity.
    
    Returns:
        MetricIndividualEntity: A test metric individual entity with sample data.
    """
    predicted_result = ConnectorResponseEntity(
        response="The answer is 42",
        context=["Context 1", "Context 2"]
    )
    
    return MetricIndividualEntity(
        prompt="What is the answer?",
        predicted_result=predicted_result,
        target="42",
        reference_context="The answer should be 42",
        evaluated_result={}
    )

# ================================
# Test __init__
# ================================
def test_init_success(mocker):
    """
    Test successful initialization of ContextRecallAdapter.
    """
    mock_config = mocker.MagicMock()
    mock_connector = mocker.MagicMock()
    
    def mock_get_metric_config(self, metric_id):
        return mock_config
    
    def mock_get_metric_connectors(self, config):
        return {"metric": mock_connector}
    
    mocker.patch("pathlib.Path.stem", "context_recall")
    mocker.patch.object(ContextRecallAdapter, 'get_metric_config', mock_get_metric_config)
    mocker.patch.object(ContextRecallAdapter, 'get_metric_connectors', mock_get_metric_connectors)
    
    adapter = ContextRecallAdapter()
    
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
    
    mocker.patch("pathlib.Path.stem", "context_recall")
    mocker.patch.object(ContextRecallAdapter, 'get_metric_config', mock_get_metric_config)
    mocker.patch('adapters.metric.context_recall_adapter.logger', mock_logger)
    
    with pytest.raises(Exception):
        ContextRecallAdapter()
    
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
    mock_config.connector_configurations.connector_adapter = "langchain_openai_chatopenai"
    mock_connector = mocker.MagicMock()
    mock_module_loader = mocker.MagicMock()
    
    mock_module_loader.load.return_value = (mock_connector, None)
    mocker.patch('adapters.metric.context_recall_adapter.ModuleLoader', mock_module_loader)
    
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    result = adapter.get_metric_connectors(mock_config)
    
    assert result == {"metric": mock_connector}
    mock_connector.configure.assert_called_once()

def test_get_metric_connectors_no_adapter(mocker):
    """
    Test get_metric_connectors when no connector adapter is specified.
    """
    mock_config = mocker.MagicMock()
    mock_config.connector_configurations.connector_adapter = ""
    
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    result = adapter.get_metric_connectors(mock_config)
    
    assert result is None

def test_get_metric_connectors_exception(mocker):
    """
    Test exception handling in get_metric_connectors.
    """
    mock_config = mocker.MagicMock()
    mock_config.connector_configurations.connector_adapter = "langchain_openai_chatopenai"
    mock_module_loader = mocker.MagicMock()
    mock_logger = mocker.MagicMock()
    
    mock_module_loader.load.side_effect = Exception("Module error")
    mocker.patch('adapters.metric.context_recall_adapter.ModuleLoader', mock_module_loader)
    mocker.patch('adapters.metric.context_recall_adapter.logger', mock_logger)
    
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    
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
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    test_params = {"threshold": 0.8}
    
    adapter.update_metric_params(test_params)
    
    assert adapter.params == test_params

def test_update_metric_params_empty():
    """
    Test updating with empty parameters.
    """
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    
    adapter.update_metric_params({})
    
    assert not hasattr(adapter, 'params')

# ================================
# Test get_individual_result
# ================================
@pytest.mark.asyncio
async def test_get_individual_result_success(metric_individual_entity, mocker):
    """
    Test successful get_individual_result.
    """
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    
    # Mock the connector and dependencies
    mock_connector = mocker.MagicMock()
    mock_llm_client = mocker.MagicMock()
    mock_connector.get_client.return_value = mock_llm_client
    adapter.selected_metric_connector = mock_connector
    
    mock_score = 0.85
    
    mock_wrapper = mocker.patch('adapters.metric.context_recall_adapter.LangchainLLMWrapper')
    mock_sample = mocker.patch('adapters.metric.context_recall_adapter.SingleTurnSample')
    mock_scorer = mocker.patch('adapters.metric.context_recall_adapter.LLMContextRecall')
    
    mock_wrapper_instance = mocker.MagicMock()
    mock_wrapper.return_value = mock_wrapper_instance
    
    mock_sample_instance = mocker.MagicMock()
    mock_sample.return_value = mock_sample_instance
    
    mock_scorer_instance = mocker.MagicMock()
    mock_scorer.return_value = mock_scorer_instance
    mock_scorer_instance.single_turn_ascore = mocker.AsyncMock(return_value=mock_score)
    
    result = await adapter.get_individual_result(metric_individual_entity)
    
    expected_result = {
        "prompt": "What is the answer?",
        "predicted_value": "The answer is 42",
        "reference_context": "The answer should be 42",
        "context": ["Context 1", "Context 2"],
        "target": "42",
        "score": 0.85
    }
    
    assert result == expected_result
    mock_scorer_instance.single_turn_ascore.assert_called_once()

@pytest.mark.asyncio
async def test_get_individual_result_no_connector(mocker):
    """
    Test get_individual_result when no connector is available.
    """
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    adapter.selected_metric_connector = None
    
    entity = mocker.MagicMock()
    
    with pytest.raises(RuntimeError):
        await adapter.get_individual_result(entity)

# ================================
# Test get_results
# ================================
@pytest.mark.asyncio
async def test_get_results_success():
    """
    Test successful get_results with multiple entities.
    """
    entities = []
    scores = [0.8, 0.9, 0.7]
    
    for i, score in enumerate(scores):
        entity = MetricIndividualEntity(
            prompt=f"Prompt {i}",
            predicted_result=ConnectorResponseEntity(response=f"Answer {i}", context=[]),
            target=f"Target {i}",
            reference_context=f"Reference {i}",
            evaluated_result={"score": score}
        )
        entities.append(entity)
    
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    
    result = await adapter.get_results(entities)
    
    expected_average = sum(scores) / len(scores)  # 0.8
    expected_result = {
        "context_recall": {
            "average_score": expected_average
        }
    }
    
    assert result == expected_result

@pytest.mark.asyncio
async def test_get_results_missing_scores():
    """
    Test get_results when some entities don't have scores.
    """
    entities = [
        MetricIndividualEntity(
            prompt="Prompt 1",
            predicted_result=ConnectorResponseEntity(response="Answer 1", context=[]),
            target="Target 1",
            reference_context="Reference 1",
            evaluated_result={"score": 0.8}
        ),
        MetricIndividualEntity(
            prompt="Prompt 2",
            predicted_result=ConnectorResponseEntity(response="Answer 2", context=[]),
            target="Target 2", 
            reference_context="Reference 2",
            evaluated_result={}  # No score
        )
    ]
    
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    
    result = await adapter.get_results(entities)
    
    # Should use 0 for missing scores: (0.8 + 0) / 2 = 0.4
    expected_result = {
        "context_recall": {
            "average_score": 0.4
        }
    }
    
    assert result == expected_result

@pytest.mark.asyncio
async def test_get_results_exception(mocker):
    """
    Test exception handling in get_results.
    """
    adapter = ContextRecallAdapter.__new__(ContextRecallAdapter)
    mock_logger = mocker.MagicMock()
    
    mocker.patch('adapters.metric.context_recall_adapter.logger', mock_logger)
    
    with pytest.raises(ZeroDivisionError):
        await adapter.get_results([])
    
    mock_logger.error.assert_called_once()