from pathlib import Path

import pytest

from adapters.metric.sg_uc_classifier_adapter import SgUcClassifierAdapter
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity


class TestSgUcClassifierAdapter:
    """Test suite for SgUcClassifierAdapter class."""

    @pytest.fixture
    def mock_metric_config(self):
        """Create a mock metric configuration entity."""
        connector_config = ConnectorEntity(
            connector_adapter="test-adapter",
            model="test-model",
        )
        return MetricConfigEntity(
            name="sg_uc_classifier_adapter",
            connector_configurations=connector_config,
        )

    @pytest.fixture
    def mock_connector_instance(self):
        """Create a mock connector instance."""

        class MockConnector:
            def __init__(self):
                self.configured = False
                self.should_return_none = False
                self.should_raise_exception = False
                self.response_value = "safe"

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
        """Create a mock metric individual entity."""
        predicted_result = ConnectorResponseEntity(
            response="This is a harmless response."
        )
        return MetricIndividualEntity(
            prompt="Test prompt",
            predicted_result=predicted_result,
            target="safe",
            evaluated_result={},
        )

    def test_init_success(
        self, monkeypatch, mock_metric_config, mock_connector_instance
    ):
        """Test successful initialization of SgUcClassifierAdapter."""

        def mock_get_metric_config(self, metric_id):
            return mock_metric_config

        def mock_module_loader_load(adapter, module_type):
            return mock_connector_instance, None

        monkeypatch.setattr(Path, "stem", "sg_uc_classifier_adapter")
        monkeypatch.setattr(
            SgUcClassifierAdapter,
            "get_metric_config",
            mock_get_metric_config,
        )
        monkeypatch.setattr(
            "adapters.metric.sg_uc_classifier_adapter.ModuleLoader.load",
            mock_module_loader_load,
        )

        adapter = SgUcClassifierAdapter()

        assert adapter.metric_config == mock_metric_config
        assert "a" in adapter.metric_connectors
        assert adapter.selected_metric_connector == mock_connector_instance

    def test_init_failure_no_metric_config(self, monkeypatch):
        """Test initialization when no metric config is found."""

        def mock_get_metric_config(self, metric_id):
            return None

        monkeypatch.setattr(Path, "stem", "sg_uc_classifier_adapter")
        monkeypatch.setattr(
            SgUcClassifierAdapter,
            "get_metric_config",
            mock_get_metric_config,
        )

        adapter = SgUcClassifierAdapter()

        assert not hasattr(adapter, "metric_connectors")

    def test_init_failure_exception(self, monkeypatch):
        """Test initialization when an exception occurs."""

        def mock_get_metric_config(self, metric_id):
            raise Exception("Test exception")

        monkeypatch.setattr(Path, "stem", "sg_uc_classifier_adapter")
        monkeypatch.setattr(
            SgUcClassifierAdapter,
            "get_metric_config",
            mock_get_metric_config,
        )

        with pytest.raises(Exception, match=r".*Test exception.*"):
            SgUcClassifierAdapter()

    def test_get_metric_connectors_success(
        self, monkeypatch, mock_metric_config, mock_connector_instance
    ):
        """Test successful retrieval of metric connectors."""

        def mock_module_loader_load(adapter, module_type):
            return mock_connector_instance, None

        monkeypatch.setattr(
            "adapters.metric.sg_uc_classifier_adapter.ModuleLoader.load",
            mock_module_loader_load,
        )

        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)
        result = adapter.get_metric_connectors(mock_metric_config)

        assert "a" in result
        assert result["a"] == mock_connector_instance
        assert mock_connector_instance.configured is True

    def test_get_metric_connectors_failure(self, monkeypatch, mock_metric_config):
        """Test failure in retrieving metric connectors."""

        def mock_module_loader_load(adapter, module_type):
            raise Exception("Connector load failed")

        monkeypatch.setattr(
            "adapters.metric.sg_uc_classifier_adapter.ModuleLoader.load",
            mock_module_loader_load,
        )

        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)

        with pytest.raises(Exception, match="Connector load failed"):
            adapter.get_metric_connectors(mock_metric_config)

    def test_update_metric_params_with_params(self):
        """Test updating metric parameters when params are provided."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)
        params = {"test_param": "test_value"}

        adapter.update_metric_params(params)

        assert adapter.params == params

    def test_update_metric_params_without_params(self):
        """Test updating metric parameters when no params are provided."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)

        adapter.update_metric_params({})
        adapter.update_metric_params(None)

    def test_normalise_guard_response(self):
        """Test _normalise_guard_response static method."""
        assert SgUcClassifierAdapter._normalise_guard_response("safe") == "safe"
        assert SgUcClassifierAdapter._normalise_guard_response("Safe") == "safe"
        assert SgUcClassifierAdapter._normalise_guard_response("unsafe") == "unsafe"
        assert (
            SgUcClassifierAdapter._normalise_guard_response("Unsafe content")
            == "unsafe"
        )
        assert SgUcClassifierAdapter._normalise_guard_response("unknown") == "unknown"
        assert SgUcClassifierAdapter._normalise_guard_response("other") == "unknown"
        assert SgUcClassifierAdapter._normalise_guard_response("") == "unknown"
        assert SgUcClassifierAdapter._normalise_guard_response("  ") == "unknown"

    @pytest.mark.asyncio
    async def test_get_individual_result_safe(
        self, mock_metric_individual_entity, mock_connector_instance
    ):
        """Test individual result when guard returns safe."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)
        mock_connector_instance.response_value = "safe"
        adapter.selected_metric_connector = mock_connector_instance

        result = await adapter.get_individual_result(mock_metric_individual_entity)

        assert result["evaluated_response"] == "safe"
        assert result["accuracy"] is True
        assert result["score"] == 1.0
        assert result["prompt"] == "Test prompt"
        assert result["predicted_value"] == "This is a harmless response."
        assert "Agent: This is a harmless response." in result["evaluated_prompt"]

    @pytest.mark.asyncio
    async def test_get_individual_result_unsafe(
        self, mock_metric_individual_entity, mock_connector_instance
    ):
        """Test individual result when guard returns unsafe."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)
        mock_connector_instance.response_value = "unsafe"
        adapter.selected_metric_connector = mock_connector_instance

        result = await adapter.get_individual_result(mock_metric_individual_entity)

        assert result["evaluated_response"] == "unsafe"
        assert result["score"] == 0

    @pytest.mark.asyncio
    async def test_get_individual_result_unknown(
        self, mock_metric_individual_entity, mock_connector_instance
    ):
        """Test individual result when guard returns unknown."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)
        mock_connector_instance.response_value = "unclear"
        adapter.selected_metric_connector = mock_connector_instance

        result = await adapter.get_individual_result(mock_metric_individual_entity)

        assert result["evaluated_response"] == "unknown"
        assert result["accuracy"] is False
        assert result["score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_individual_result_no_connector(
        self, mock_metric_individual_entity
    ):
        """Test individual result when no connector is available."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)
        adapter.selected_metric_connector = None

        with pytest.raises(
            RuntimeError,
            match="No metric connector available for evaluation",
        ):
            await adapter.get_individual_result(mock_metric_individual_entity)

    @pytest.mark.asyncio
    async def test_get_individual_result_no_model_predictions(
        self, mock_metric_individual_entity, mock_connector_instance
    ):
        """Test individual result when model returns None."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)
        mock_connector_instance.should_return_none = True
        adapter.selected_metric_connector = mock_connector_instance

        with pytest.raises(
            RuntimeError,
            match="Failed to get model predictions from the evaluation model",
        ):
            await adapter.get_individual_result(mock_metric_individual_entity)

    @pytest.mark.asyncio
    async def test_get_individual_result_exception(
        self, mock_metric_individual_entity, mock_connector_instance
    ):
        """Test individual result when connector raises."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)
        mock_connector_instance.should_raise_exception = True
        adapter.selected_metric_connector = mock_connector_instance

        with pytest.raises(Exception, match="Connection failed"):
            await adapter.get_individual_result(mock_metric_individual_entity)

    @pytest.mark.asyncio
    async def test_get_results_success(self):
        """Test aggregated results with mixed safe/unsafe/unknown."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)

        entities = []
        for i, cat in enumerate(["safe", "safe", "unsafe", "unknown", "safe"]):
            entity = MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=ConnectorResponseEntity(response=f"R{i}"),
                target="safe",
                evaluated_result={"evaluated_response": cat},
            )
            entities.append(entity)

        result = await adapter.get_results(entities)

        assert result == {"Safety": {"safe_rate": 60.0}}  # 3/5 safe

    @pytest.mark.asyncio
    async def test_get_results_all_safe(self):
        """Test aggregated results when all are safe."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)

        entities = [
            MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=ConnectorResponseEntity(response=f"R{i}"),
                target="safe",
                evaluated_result={"evaluated_response": "safe"},
            )
            for i in range(3)
        ]

        result = await adapter.get_results(entities)

        assert result == {"Safety": {"safe_rate": 100.0}}

    @pytest.mark.asyncio
    async def test_get_results_all_unsafe(self):
        """Test aggregated results when all are unsafe."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)

        entities = [
            MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=ConnectorResponseEntity(response=f"R{i}"),
                target="safe",
                evaluated_result={"evaluated_response": "unsafe"},
            )
            for i in range(3)
        ]

        result = await adapter.get_results(entities)

        assert result == {"Safety": {"safe_rate": 0.0}}

    @pytest.mark.asyncio
    async def test_get_results_empty_list(self):
        """Test aggregated results with empty entity list (refusal_rate 0)."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)

        result = await adapter.get_results([])

        assert result == {"Safety": {"safe_rate": 0.0}}

    @pytest.mark.asyncio
    async def test_get_results_missing_evaluated_response(self):
        """Test aggregation when evaluated_result lacks evaluated_response."""
        adapter = SgUcClassifierAdapter.__new__(SgUcClassifierAdapter)

        entity = MetricIndividualEntity(
            prompt="Test",
            predicted_result=ConnectorResponseEntity(response="R"),
            target="safe",
            evaluated_result={},  # no evaluated_response
        )

        result = await adapter.get_results([entity])

        assert result == {"Safety": {"safe_rate": 0.0}}
