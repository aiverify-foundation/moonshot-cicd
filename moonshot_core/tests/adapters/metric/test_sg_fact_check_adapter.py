from pathlib import Path

import pytest

from adapters.metric.sg_fact_check_adapter import SgFactCheckAdapter
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity


class TestSgFactCheckAdapter:
    """Test suite for SgFactCheckAdapter class."""

    @pytest.fixture
    def mock_metric_config(self):
        """Create a mock metric configuration entity."""
        connector_config = ConnectorEntity(
            connector_adapter="test-adapter",
            model="test-model",
        )
        return MetricConfigEntity(
            name="sg_fact_check_adapter",
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
                self.response_value = "True"

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
            response="Singapore has four official languages."
        )
        return MetricIndividualEntity(
            prompt="What are Singapore's official languages?",
            predicted_result=predicted_result,
            target="Singapore has four official languages: English, Malay, Chinese, and Tamil.",
            evaluated_result={},
        )

    def test_init_success(
        self, monkeypatch, mock_metric_config, mock_connector_instance
    ):
        """Test successful initialization of SgFactCheckAdapter."""

        def mock_get_metric_config(self, metric_id):
            return mock_metric_config

        def mock_module_loader_load(adapter, module_type):
            return mock_connector_instance, None

        monkeypatch.setattr(Path, "stem", "sg_fact_check_adapter")
        monkeypatch.setattr(
            SgFactCheckAdapter,
            "get_metric_config",
            mock_get_metric_config,
        )
        monkeypatch.setattr(
            "adapters.metric.sg_fact_check_adapter.ModuleLoader.load",
            mock_module_loader_load,
        )

        adapter = SgFactCheckAdapter()

        assert adapter.metric_config == mock_metric_config
        assert "a" in adapter.metric_connectors
        assert adapter.selected_metric_connector == mock_connector_instance

    def test_init_failure_no_metric_config(self, monkeypatch):
        """Test initialization when no metric config is found."""

        def mock_get_metric_config(self, metric_id):
            return None

        monkeypatch.setattr(Path, "stem", "sg_fact_check_adapter")
        monkeypatch.setattr(
            SgFactCheckAdapter,
            "get_metric_config",
            mock_get_metric_config,
        )

        adapter = SgFactCheckAdapter()

        assert not hasattr(adapter, "metric_connectors")

    def test_init_failure_exception(self, monkeypatch):
        """Test initialization when an exception occurs."""

        def mock_get_metric_config(self, metric_id):
            raise Exception("Test exception")

        monkeypatch.setattr(Path, "stem", "sg_fact_check_adapter")
        monkeypatch.setattr(
            SgFactCheckAdapter,
            "get_metric_config",
            mock_get_metric_config,
        )

        with pytest.raises(Exception, match=r".*Test exception.*"):
            SgFactCheckAdapter()

    def test_get_metric_connectors_success(
        self, monkeypatch, mock_metric_config, mock_connector_instance
    ):
        """Test successful retrieval of metric connectors."""

        def mock_module_loader_load(adapter, module_type):
            return mock_connector_instance, None

        monkeypatch.setattr(
            "adapters.metric.sg_fact_check_adapter.ModuleLoader.load",
            mock_module_loader_load,
        )

        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
        result = adapter.get_metric_connectors(mock_metric_config)

        assert "a" in result
        assert result["a"] == mock_connector_instance
        assert mock_connector_instance.configured is True

    def test_get_metric_connectors_failure(self, monkeypatch, mock_metric_config):
        """Test failure in retrieving metric connectors."""

        def mock_module_loader_load(adapter, module_type):
            raise Exception("Connector load failed")

        monkeypatch.setattr(
            "adapters.metric.sg_fact_check_adapter.ModuleLoader.load",
            mock_module_loader_load,
        )

        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)

        with pytest.raises(Exception, match="Connector load failed"):
            adapter.get_metric_connectors(mock_metric_config)

    def test_update_metric_params_with_params(self):
        """Test updating metric parameters when params are provided."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
        params = {"test_param": "test_value"}

        adapter.update_metric_params(params)

        assert adapter.params == params

    def test_update_metric_params_without_params(self):
        """Test updating metric parameters when no params are provided."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)

        adapter.update_metric_params({})
        adapter.update_metric_params(None)

    def test_normalise_judge_response(self):
        """Test _normalise_judge_response static method."""
        assert SgFactCheckAdapter._normalise_judge_response("True") == "True"
        assert SgFactCheckAdapter._normalise_judge_response("true") == "True"
        assert SgFactCheckAdapter._normalise_judge_response("False") == "False"
        assert SgFactCheckAdapter._normalise_judge_response("false") == "False"
        assert SgFactCheckAdapter._normalise_judge_response("Verdict: False") == "False"
        # false before true when both appear
        assert SgFactCheckAdapter._normalise_judge_response("True or False?") == "False"
        assert SgFactCheckAdapter._normalise_judge_response("unknown") == "unknown"
        assert SgFactCheckAdapter._normalise_judge_response("other") == "unknown"
        assert SgFactCheckAdapter._normalise_judge_response("") == "unknown"
        assert SgFactCheckAdapter._normalise_judge_response("  ") == "unknown"

    @pytest.mark.asyncio
    async def test_get_individual_result_true(
        self, mock_metric_individual_entity, mock_connector_instance
    ):
        """Test individual result when judge returns True."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
        mock_connector_instance.response_value = "True"
        adapter.selected_metric_connector = mock_connector_instance

        result = await adapter.get_individual_result(mock_metric_individual_entity)

        assert result["evaluated_response"] == "True"
        assert result["accuracy"] is True
        assert result["score"] == 1.0
        assert result["prompt"] == "What are Singapore's official languages?"
        assert result["predicted_value"] == "Singapore has four official languages."
        assert (
            "Answer: Singapore has four official languages."
            in result["evaluated_prompt"]
        )
        assert "Ground truth:" in result["evaluated_prompt"]

    @pytest.mark.asyncio
    async def test_get_individual_result_false(
        self, mock_metric_individual_entity, mock_connector_instance
    ):
        """Test individual result when judge returns False."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
        mock_connector_instance.response_value = "False"
        adapter.selected_metric_connector = mock_connector_instance

        result = await adapter.get_individual_result(mock_metric_individual_entity)

        assert result["evaluated_response"] == "False"
        assert result["accuracy"] is False
        assert result["score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_individual_result_unknown(
        self, mock_metric_individual_entity, mock_connector_instance
    ):
        """Test individual result when judge returns unknown."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
        mock_connector_instance.response_value = "unclear"
        adapter.selected_metric_connector = mock_connector_instance

        result = await adapter.get_individual_result(mock_metric_individual_entity)

        assert result["evaluated_response"] == "unknown"
        assert result["accuracy"] is False
        assert result["score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_individual_result_invalid_entity(self, mock_connector_instance):
        """Test individual result when entity is missing required fields."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
        adapter.selected_metric_connector = mock_connector_instance
        entity = MetricIndividualEntity(
            prompt="",
            predicted_result=ConnectorResponseEntity(response=""),
            target="",
            evaluated_result={},
        )

        with pytest.raises(ValueError, match="Invalid entity"):
            await adapter.get_individual_result(entity)

    @pytest.mark.asyncio
    async def test_get_individual_result_no_connector(
        self, mock_metric_individual_entity
    ):
        """Test individual result when no connector is available."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
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
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
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
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)
        mock_connector_instance.should_raise_exception = True
        adapter.selected_metric_connector = mock_connector_instance

        with pytest.raises(Exception, match="Connection failed"):
            await adapter.get_individual_result(mock_metric_individual_entity)

    @pytest.mark.asyncio
    async def test_get_results_success(self):
        """Test aggregated results with mixed True/False/unknown."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)

        entities = []
        for i, cat in enumerate(["True", "True", "False", "unknown", "True"]):
            entity = MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=ConnectorResponseEntity(response=f"R{i}"),
                target="gt",
                evaluated_result={"evaluated_response": cat},
            )
            entities.append(entity)

        result = await adapter.get_results(entities)

        assert result == {"FactCheck": {"true_rate": 60.0}}  # 3/5 True

    @pytest.mark.asyncio
    async def test_get_results_all_true(self):
        """Test aggregated results when all are True."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)

        entities = [
            MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=ConnectorResponseEntity(response=f"R{i}"),
                target="gt",
                evaluated_result={"evaluated_response": "True"},
            )
            for i in range(3)
        ]

        result = await adapter.get_results(entities)

        assert result == {"FactCheck": {"true_rate": 100.0}}

    @pytest.mark.asyncio
    async def test_get_results_all_false(self):
        """Test aggregated results when all are False."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)

        entities = [
            MetricIndividualEntity(
                prompt=f"Test prompt {i}",
                predicted_result=ConnectorResponseEntity(response=f"R{i}"),
                target="gt",
                evaluated_result={"evaluated_response": "False"},
            )
            for i in range(3)
        ]

        result = await adapter.get_results(entities)

        assert result == {"FactCheck": {"true_rate": 0.0}}

    @pytest.mark.asyncio
    async def test_get_results_empty_list(self):
        """Test aggregated results with empty entity list."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)

        result = await adapter.get_results([])

        assert result == {"FactCheck": {"true_rate": 0.0}}

    @pytest.mark.asyncio
    async def test_get_results_missing_evaluated_response(self):
        """Test aggregation when evaluated_result lacks evaluated_response."""
        adapter = SgFactCheckAdapter.__new__(SgFactCheckAdapter)

        entity = MetricIndividualEntity(
            prompt="Test",
            predicted_result=ConnectorResponseEntity(response="R"),
            target="gt",
            evaluated_result={},
        )

        result = await adapter.get_results([entity])

        assert result == {"FactCheck": {"true_rate": 0.0}}
