import pytest
from adapters.metric.faithfulness_adapter import FaithfulnessAdapter
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
        response="The sky appears blue due to Rayleigh scattering.",
        context=["The atmosphere scatters shorter wavelengths more than longer ones.", 
                "Blue light has a shorter wavelength than red light."]
    )
    
    return MetricIndividualEntity(
        prompt="Why is the sky blue?",
        predicted_result=predicted_result,
        target="Due to atmospheric scattering",
        evaluated_result={}
    )


@pytest.fixture
def multiple_entities():
    """
    Create multiple test entities with different scores.
    
    Returns:
        list: A list of MetricIndividualEntity objects with varying scores.
    """
    entities = []
    scores = [0.8, 0.9, 0.7, 0.6]
    
    for i, score in enumerate(scores):
        predicted_result = ConnectorResponseEntity(
            response=f"Response {i}",
            context=[f"Context {i}.1", f"Context {i}.2"]
        )
        entity = MetricIndividualEntity(
            prompt=f"Prompt {i}",
            predicted_result=predicted_result,
            target=f"Target {i}",
            evaluated_result={"score": score}
        )
        entities.append(entity)
    
    return entities


# ================================
# Test __init__
# ================================
def test_init_success(mocker):
    """
    Test successful initialization of FaithfulnessAdapter.
    """
    mock_config = mocker.MagicMock()
    mock_connector = mocker.MagicMock()
    
    mocker.patch("pathlib.Path.stem", "faithfulness")
    mocker.patch.object(FaithfulnessAdapter, 'get_metric_config', return_value=mock_config)
    mocker.patch.object(FaithfulnessAdapter, 'get_metric_connectors', return_value={"metric": mock_connector})
    
    adapter = FaithfulnessAdapter()
    
    assert adapter.metric_config == mock_config
    assert adapter.metric_connectors == {"metric": mock_connector}
    assert adapter.selected_metric_connector == mock_connector


def test_init_no_connectors(mocker):
    """
    Test initialization when no connectors are available.
    """
    mock_config = mocker.MagicMock()
    
    mocker.patch("pathlib.Path.stem", "faithfulness")
    mocker.patch.object(FaithfulnessAdapter, 'get_metric_config', return_value=mock_config)
    mocker.patch.object(FaithfulnessAdapter, 'get_metric_connectors', return_value=None)
    
    adapter = FaithfulnessAdapter()
    
    assert adapter.metric_config == mock_config


def test_init_no_config(mocker):
    """
    Test initialization when no config is available.
    """
    mocker.patch("pathlib.Path.stem", "faithfulness")
    mocker.patch.object(FaithfulnessAdapter, 'get_metric_config', return_value=None)
    
    adapter = FaithfulnessAdapter()
    
    assert adapter.metric_config is None


def test_init_exception_handling(mocker):
    """
    Test initialization exception handling.
    """
    mock_logger = mocker.MagicMock()
    
    mocker.patch("pathlib.Path.stem", "faithfulness")
    mocker.patch.object(FaithfulnessAdapter, 'get_metric_config', side_effect=Exception("Config error"))
    mocker.patch('adapters.metric.faithfulness_adapter.logger', mock_logger)
    
    with pytest.raises(Exception):
        FaithfulnessAdapter()
    
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
    mock_module_loader = mocker.patch('adapters.metric.faithfulness_adapter.ModuleLoader')
    mock_logger = mocker.patch('adapters.metric.faithfulness_adapter.logger')
    
    mock_module_loader.load.return_value = (mock_connector, None)
    
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    result = adapter.get_metric_connectors(mock_config)
    
    assert result == {"metric": mock_connector}
    mock_connector.configure.assert_called_once_with(mock_config.connector_configurations)
    mock_logger.info.assert_called()


def test_get_metric_connectors_no_adapter(mocker):
    """
    Test get_metric_connectors when no connector adapter is specified.
    """
    mock_config = mocker.MagicMock()
    mock_config.connector_configurations.connector_adapter = None
    
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    result = adapter.get_metric_connectors(mock_config)
    
    assert result is None


def test_get_metric_connectors_exception(mocker):
    """
    Test exception handling in get_metric_connectors.
    """
    mock_config = mocker.MagicMock()
    mock_config.connector_configurations.connector_adapter = "langchain_openai_chatopenai"
    mock_module_loader = mocker.patch('adapters.metric.faithfulness_adapter.ModuleLoader')
    mock_logger = mocker.patch('adapters.metric.faithfulness_adapter.logger')
    
    mock_module_loader.load.side_effect = Exception("Module error")
    
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    
    with pytest.raises(Exception):
        adapter.get_metric_connectors(mock_config)
    
    mock_logger.error.assert_called_once()


# ================================
# Test update_metric_params
# ================================
@pytest.mark.parametrize("params,expected", [
    ({"threshold": 0.8, "model": "gpt-4"}, {"threshold": 0.8, "model": "gpt-4"}),
    ({"temperature": 0.5}, {"temperature": 0.5}),
    ({}, None),
    (None, None),
])
def test_update_metric_params(params, expected):
    """
    Test updating metric parameters with various inputs.
    """
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    
    adapter.update_metric_params(params)
    
    if expected:
        assert adapter.params == expected
    else:
        assert not hasattr(adapter, 'params')


# ================================
# Test get_individual_result
# ================================
@pytest.mark.asyncio
async def test_get_individual_result_success(metric_individual_entity, mocker):
    """
    Test successful get_individual_result.
    """
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    
    # Mock the connector and dependencies
    mock_connector = mocker.MagicMock()
    mock_llm_client = mocker.MagicMock()
    mock_connector.get_client.return_value = mock_llm_client
    adapter.selected_metric_connector = mock_connector
    
    mock_score = 0.85
    
    mock_wrapper = mocker.patch('adapters.metric.faithfulness_adapter.LangchainLLMWrapper')
    mock_sample = mocker.patch('adapters.metric.faithfulness_adapter.SingleTurnSample')
    mock_faithfulness = mocker.patch('adapters.metric.faithfulness_adapter.Faithfulness')
    
    mock_wrapper_instance = mocker.MagicMock()
    mock_wrapper.return_value = mock_wrapper_instance
    
    mock_sample_instance = mocker.MagicMock()
    mock_sample.return_value = mock_sample_instance
    
    mock_scorer_instance = mocker.MagicMock()
    mock_faithfulness.return_value = mock_scorer_instance
    mock_scorer_instance.single_turn_ascore = mocker.AsyncMock(return_value=mock_score)
    
    result = await adapter.get_individual_result(metric_individual_entity)
    
    expected_result = {
        "prompt": "Why is the sky blue?",
        "predicted_value": "The sky appears blue due to Rayleigh scattering.",
        "context": ["The atmosphere scatters shorter wavelengths more than longer ones.", 
                   "Blue light has a shorter wavelength than red light."],
        "target": "Due to atmospheric scattering",
        "score": 0.85
    }
    
    assert result == expected_result
    mock_sample.assert_called_once_with(
        user_input="Why is the sky blue?",
        response="The sky appears blue due to Rayleigh scattering.",
        retrieved_contexts=["The atmosphere scatters shorter wavelengths more than longer ones.", 
                          "Blue light has a shorter wavelength than red light."]
    )
    mock_scorer_instance.single_turn_ascore.assert_called_once()


@pytest.mark.asyncio
async def test_get_individual_result_no_connector(mocker):
    """
    Test get_individual_result when no connector is available.
    """
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    adapter.selected_metric_connector = None
    
    entity = mocker.MagicMock()
    
    with pytest.raises(RuntimeError) as exc_info:
        await adapter.get_individual_result(entity)
    
    assert "No metric connector available for evaluation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_individual_result_scoring_exception(metric_individual_entity, mocker):
    """
    Test get_individual_result when scoring fails.
    """
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    
    mock_connector = mocker.MagicMock()
    mock_llm_client = mocker.MagicMock()
    mock_connector.get_client.return_value = mock_llm_client
    adapter.selected_metric_connector = mock_connector
    
    mock_wrapper = mocker.patch('adapters.metric.faithfulness_adapter.LangchainLLMWrapper')
    mock_sample = mocker.patch('adapters.metric.faithfulness_adapter.SingleTurnSample')
    mock_faithfulness = mocker.patch('adapters.metric.faithfulness_adapter.Faithfulness')
    
    mock_scorer_instance = mocker.MagicMock()
    mock_faithfulness.return_value = mock_scorer_instance
    mock_scorer_instance.single_turn_ascore = mocker.AsyncMock(side_effect=Exception("Scoring error"))
    
    with pytest.raises(Exception, match="Scoring error"):
        await adapter.get_individual_result(metric_individual_entity)


# ================================
# Test get_results
# ================================
@pytest.mark.asyncio
@pytest.mark.parametrize("scores,expected_average", [
    ([0.8, 0.9, 0.7, 0.6], 0.75),
    ([1.0, 1.0, 1.0], 1.0),
    ([0.0, 0.0, 0.0], 0.0),
    ([0.5], 0.5),
    ([0.25, 0.75], 0.5),
])
async def test_get_results_various_scores(scores, expected_average):
    """
    Test get_results with various score combinations.
    """
    entities = []
    
    for i, score in enumerate(scores):
        predicted_result = ConnectorResponseEntity(
            response=f"Response {i}",
            context=[f"Context {i}"]
        )
        entity = MetricIndividualEntity(
            prompt=f"Prompt {i}",
            predicted_result=predicted_result,
            target=f"Target {i}",
            evaluated_result={"score": score}
        )
        entities.append(entity)
    
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    
    result = await adapter.get_results(entities)
    
    assert result["faithfulness"]["average_score"] == pytest.approx(expected_average)


@pytest.mark.asyncio
async def test_get_results_success(multiple_entities):
    """
    Test successful get_results with multiple entities.
    """
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    
    result = await adapter.get_results(multiple_entities)
    
    expected_average = (0.8 + 0.9 + 0.7 + 0.6) / 4
    assert result["faithfulness"]["average_score"] == pytest.approx(expected_average)


@pytest.mark.asyncio
async def test_get_results_missing_scores():
    """
    Test get_results when some entities have missing scores.
    """
    entities = []
    
    # Entity with score
    predicted_result1 = ConnectorResponseEntity(response="Response 1", context=["Context 1"])
    entity1 = MetricIndividualEntity(
        prompt="Prompt 1",
        predicted_result=predicted_result1,
        target="Target 1",
        evaluated_result={"score": 0.8}
    )
    
    # Entity without score
    predicted_result2 = ConnectorResponseEntity(response="Response 2", context=["Context 2"])
    entity2 = MetricIndividualEntity(
        prompt="Prompt 2",
        predicted_result=predicted_result2,
        target="Target 2",
        evaluated_result={}
    )
    
    entities = [entity1, entity2]
    
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    
    result = await adapter.get_results(entities)
    
    # Should calculate average with missing scores treated as 0
    expected_average = (0.8 + 0) / 2
    assert result["faithfulness"]["average_score"] == pytest.approx(expected_average)


@pytest.mark.asyncio
async def test_get_results_exception(mocker):
    """
    Test exception handling in get_results.
    """
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    mock_logger = mocker.patch('adapters.metric.faithfulness_adapter.logger')
    
    with pytest.raises(TypeError):
        await adapter.get_results(None)
    
    mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_get_results_empty_list():
    """
    Test get_results with empty entity list.
    """
    adapter = FaithfulnessAdapter.__new__(FaithfulnessAdapter)
    
    with pytest.raises(ZeroDivisionError):
        await adapter.get_results([])
