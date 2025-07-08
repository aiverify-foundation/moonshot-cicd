import pytest
from pathlib import Path

from adapters.metric.refusal_adapter import RefusalAdapter
from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.prompt_entity import PromptEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.connector_entity import ConnectorEntity


class TestRefusalAdapter:
    """Test suite for RefusalAdapter class."""

    @pytest.fixture
    def mock_metric_config(self):
        """
        Create a mock metric configuration entity.
        
        Returns:
            MetricConfigEntity: A test metric configuration entity.
        """
        connector_config = ConnectorEntity(
            connector_adapter="test-adapter",
            model="test-model"
        )
        mock_config = MetricConfigEntity(
            name="refusal_adapter",
            connector_configurations=connector_config
        )
        return mock_config

    @pytest.fixture
    def mock_connector_instance(self):
        """
        Create a mock connector instance.
        
        Returns:
            MockConnector: A mock connector instance for testing.
        """
        class MockConnector:
            def __init__(self):
                self.configured = False
                self.should_return_none = False
                self.should_raise_exception = False
                self.response_value = "accept"
            
            def configure(self, config):
                self.configured = True
            
            async def get_response(self, prompt_entity):
                if self.should_raise_exception:
                    raise Exception("Connection failed")
                if self.should_return_none:
                    return None
                return ConnectorResponseEntity(response=self.response_value)
        
        return MockConnector()

    @pytest.fixture
    def mock_metric_individual_entity(self):
        """
        Create a mock metric individual entity.
        
        Returns:
            MetricIndividualEntity: A test metric individual entity with sample data.
        """
        predicted_result = ConnectorResponseEntity(
            response="I cannot help with that request"
        )
        entity = MetricIndividualEntity(
            prompt="Test prompt",
            predicted_result=predicted_result,
            target="refuse",
            evaluated_result={}
        )
        return entity

    @pytest.fixture
    def mock_connector_response(self):
        """
        Create a mock connector response.
        
        Returns:
            ConnectorResponseEntity: A test connector response entity.
        """
        response = ConnectorResponseEntity(
            response="accept"
        )
        return response

    def test_init_success(self, monkeypatch, mock_metric_config, mock_connector_instance):
        """
        Test successful initialization of RefusalAdapter.
        
        Args:
            monkeypatch: Pytest fixture for patching.
            mock_metric_config: Fixture providing a mock metric configuration.
            mock_connector_instance: Fixture providing a mock connector instance.
        """
        # Mock the get_metric_config method
        def mock_get_metric_config(self, metric_id):
            return mock_metric_config

        # Mock ModuleLoader.load
        def mock_module_loader_load(adapter, module_type):
            return mock_connector_instance, None

        # Mock Path(__file__).stem
        monkeypatch.setattr(Path, "stem", "refusal_adapter")
        monkeypatch.setattr(RefusalAdapter, "get_metric_config", mock_get_metric_config)
        monkeypatch.setattr("adapters.metric.refusal_adapter.ModuleLoader.load", mock_module_loader_load)

        adapter = RefusalAdapter()

        assert adapter.metric_config == mock_metric_config
        assert "a" in adapter.metric_connectors
        assert adapter.selected_metric_connector == mock_connector_instance

    def test_init_failure_no_metric_config(self, monkeypatch):
        """
        Test initialization failure when no metric config is found.
        
        Args:
            monkeypatch: Pytest fixture for patching.
        """
        # Mock the get_metric_config method to return None
        def mock_get_metric_config(self, metric_id):
            return None

        monkeypatch.setattr(Path, "stem", "refusal_adapter")
        monkeypatch.setattr(RefusalAdapter, "get_metric_config", mock_get_metric_config)

        adapter = RefusalAdapter()
        
        # Should handle gracefully when no metric config is found
        assert not hasattr(adapter, 'metric_connectors')

    def test_init_failure_exception(self, monkeypatch):
        """
        Test initialization failure when an exception occurs.
        
        Args:
            monkeypatch: Pytest fixture for patching.
        """
        # Mock to raise an exception
        def mock_get_metric_config(self, metric_id):
            raise Exception("Test exception")

        monkeypatch.setattr(Path, "stem", "refusal_adapter")
        monkeypatch.setattr(RefusalAdapter, "get_metric_config", mock_get_metric_config)

        with pytest.raises(Exception, match=r".*Test exception.*"):
            RefusalAdapter()

    def test_get_metric_connectors_success(self, monkeypatch, mock_metric_config, mock_connector_instance):
        """
        Test successful retrieval of metric connectors.
        
        Args:
            monkeypatch: Pytest fixture for patching.
            mock_metric_config: Fixture providing a mock metric configuration.
            mock_connector_instance: Fixture providing a mock connector instance.
        """
        # Mock ModuleLoader.load
        def mock_module_loader_load(adapter, module_type):
            return mock_connector_instance, None

        monkeypatch.setattr("adapters.metric.refusal_adapter.ModuleLoader.load", mock_module_loader_load)

        adapter = RefusalAdapter.__new__(RefusalAdapter)
        result = adapter.get_metric_connectors(mock_metric_config)

        assert "a" in result
        assert result["a"] == mock_connector_instance
        assert mock_connector_instance.configured is True

    def test_get_metric_connectors_failure(self, monkeypatch, mock_metric_config):
        """
        Test failure in retrieving metric connectors.
        
        Args:
            monkeypatch: Pytest fixture for patching.
            mock_metric_config: Fixture providing a mock metric configuration.
        """
        # Mock ModuleLoader.load to raise an exception
        def mock_module_loader_load(adapter, module_type):
            raise Exception("Connector load failed")

        monkeypatch.setattr("adapters.metric.refusal_adapter.ModuleLoader.load", mock_module_loader_load)

        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        with pytest.raises(Exception, match="Connector load failed"):
            adapter.get_metric_connectors(mock_metric_config)

    def test_update_metric_params_with_params(self):
        """
        Test updating metric parameters when params are provided.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        params = {"test_param": "test_value"}
        
        adapter.update_metric_params(params)
        
        assert adapter.params == params

    def test_update_metric_params_without_params(self):
        """
        Test updating metric parameters when no params are provided.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        # Should not raise an exception
        adapter.update_metric_params({})
        adapter.update_metric_params(None)

    @pytest.mark.asyncio
    async def test_get_individual_result_success_attack_success(self, mock_metric_individual_entity, mock_connector_instance):
        """
        Test successful individual result evaluation with attack success.
        
        Args:
            mock_metric_individual_entity: Fixture providing a mock metric individual entity.
            mock_connector_instance: Fixture providing a mock connector instance.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        # Set up mock connector
        mock_connector_instance.response_value = "accept"  # Different from target "refuse"
        adapter.selected_metric_connector = mock_connector_instance

        result = await adapter.get_individual_result(mock_metric_individual_entity)

        assert result["prompt"] == "Test prompt"
        assert result["predicted_response"] == "I cannot help with that request"
        assert result["target"] == "refuse"
        assert result["evaluated_response"] == "accept"
        assert result["attack_success"] is True
        assert "Question: Test prompt\nResponse: I cannot help with that request" in result["evaluated_prompt"]

    @pytest.mark.asyncio
    async def test_get_individual_result_success_attack_failure(self, mock_metric_individual_entity, mock_connector_instance):
        """
        Test successful individual result evaluation with attack failure.
        
        Args:
            mock_metric_individual_entity: Fixture providing a mock metric individual entity.
            mock_connector_instance: Fixture providing a mock connector instance.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        # Set up mock connector
        mock_connector_instance.response_value = "refuse"  # Same as target "refuse"
        adapter.selected_metric_connector = mock_connector_instance

        result = await adapter.get_individual_result(mock_metric_individual_entity)

        assert result["attack_success"] is False

    @pytest.mark.asyncio
    async def test_get_individual_result_no_connector(self, mock_metric_individual_entity):
        """
        Test individual result evaluation when no connector is available.
        
        Args:
            mock_metric_individual_entity: Fixture providing a mock metric individual entity.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        adapter.selected_metric_connector = None

        with pytest.raises(RuntimeError, match="No metric connector available for evaluation"):
            await adapter.get_individual_result(mock_metric_individual_entity)

    @pytest.mark.asyncio
    async def test_get_individual_result_no_model_predictions(self, mock_metric_individual_entity, mock_connector_instance):
        """
        Test individual result evaluation when model predictions fail.
        
        Args:
            mock_metric_individual_entity: Fixture providing a mock metric individual entity.
            mock_connector_instance: Fixture providing a mock connector instance.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        # Set up mock connector that returns None
        mock_connector_instance.should_return_none = True
        adapter.selected_metric_connector = mock_connector_instance

        with pytest.raises(RuntimeError, match="Failed to get model predictions from the evaluation model"):
            await adapter.get_individual_result(mock_metric_individual_entity)

    @pytest.mark.asyncio
    async def test_get_individual_result_exception(self, mock_metric_individual_entity, mock_connector_instance):
        """
        Test individual result evaluation when an exception occurs.
        
        Args:
            mock_metric_individual_entity: Fixture providing a mock metric individual entity.
            mock_connector_instance: Fixture providing a mock connector instance.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        # Set up mock connector that raises an exception
        mock_connector_instance.should_raise_exception = True
        adapter.selected_metric_connector = mock_connector_instance

        with pytest.raises(Exception, match="Connection failed"):
            await adapter.get_individual_result(mock_metric_individual_entity)

    @pytest.mark.asyncio
    async def test_get_results_success(self):
        """
        Test successful aggregated results calculation.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        # Create mock entities with evaluated results
        entities = []
        for i in range(5):
            predicted_result = ConnectorResponseEntity(response=f"Response {i}")
            entity = MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=predicted_result,
                target="refuse",
                evaluated_result={"attack_success": i < 3}  # 3 successful, 2 failed
            )
            entities.append(entity)

        result = await adapter.get_results(entities)

        assert "refusal" in result
        assert result["refusal"]["attack_success_rate"] == 60.0  # 3/5 * 100

    @pytest.mark.asyncio
    async def test_get_results_all_success(self):
        """
        Test aggregated results when all attacks succeed.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        entities = []
        for i in range(3):
            predicted_result = ConnectorResponseEntity(response=f"Response {i}")
            entity = MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=predicted_result,
                target="refuse",
                evaluated_result={"attack_success": True}
            )
            entities.append(entity)

        result = await adapter.get_results(entities)

        assert result["refusal"]["attack_success_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_get_results_all_failure(self):
        """
        Test aggregated results when all attacks fail.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        entities = []
        for i in range(3):
            predicted_result = ConnectorResponseEntity(response=f"Response {i}")
            entity = MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=predicted_result,
                target="refuse",
                evaluated_result={"attack_success": False}
            )
            entities.append(entity)

        result = await adapter.get_results(entities)

        assert result["refusal"]["attack_success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_results_empty_list(self):
        """
        Test aggregated results with empty entity list.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        with pytest.raises(ZeroDivisionError):
            await adapter.get_results([])

    @pytest.mark.asyncio
    async def test_get_results_exception(self):
        """
        Test aggregated results when an exception occurs.
        """
        adapter = RefusalAdapter.__new__(RefusalAdapter)
        
        # Create an entity that will cause an exception when accessing evaluated_result
        class FaultyEntity:
            @property
            def evaluated_result(self):
                raise Exception("Access failed")

        entities = [FaultyEntity()]

        with pytest.raises(Exception, match="Access failed"):
            await adapter.get_results(entities)
