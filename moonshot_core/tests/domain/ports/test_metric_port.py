"""Tests for MetricPort binary score / result-name defaults."""

from __future__ import annotations

from domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.ports.metric_port import MetricPort


class _StubMetric(MetricPort):
    """Minimal concrete MetricPort for default-method tests."""

    def get_metric_connectors(self, metric_config_entity: MetricConfigEntity) -> dict:
        return {}

    def update_metric_params(self, params: dict) -> None:
        return None

    async def get_individual_result(self, entity: MetricIndividualEntity) -> dict:
        return {}

    async def get_results(self, entities: list[MetricIndividualEntity]) -> dict:
        return {}


class TestMetricPortScoreLabels:
    def test_default_result_constants(self):
        assert MetricPort.RESULT_UNKNOWN == "unknown"
        assert MetricPort.RESULT_PASS == "True"
        assert MetricPort.RESULT_FAIL == "False"

    def test_score_from_evaluated_response_pass(self):
        metric = _StubMetric()
        assert metric.score_from_evaluated_response("True") == 1.0

    def test_score_from_evaluated_response_fail_and_unknown_are_zero(self):
        metric = _StubMetric()
        assert metric.score_from_evaluated_response("False") == 0.0
        assert metric.score_from_evaluated_response(MetricPort.RESULT_UNKNOWN) == 0.0
        assert metric.score_from_evaluated_response("") == 0.0
        assert metric.score_from_evaluated_response("other") == 0.0

    def test_result_name_for_score(self):
        metric = _StubMetric()
        assert metric.result_name_for_score(1) == "True"
        assert metric.result_name_for_score(1.0) == "True"
        assert metric.result_name_for_score(0) == "False"
        assert metric.result_name_for_score(0.0) == "False"
        assert metric.result_name_for_score(0.5) == "False"
