"""Tests for MetricScoreLabelService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from application.dto.metric_score_label_dto import MetricScoreResultNamesDTO
from application.services.metric_score_label_service import (
    MetricScoreLabelNotFoundError,
    MetricScoreLabelService,
)
from domain.ports.metric_port import MetricPort


class _FakeMetric(MetricPort):
    RESULT_PASS = "safe"
    RESULT_FAIL = "unsafe"

    def get_metric_connectors(self, metric_config_entity):
        return {}

    def update_metric_params(self, params: dict) -> None:
        return None

    async def get_individual_result(self, entity):
        return {}

    async def get_results(self, entities):
        return {}


@pytest.fixture
def service() -> MetricScoreLabelService:
    return MetricScoreLabelService()


def test_score_from_evaluated_response(monkeypatch, service):
    fake = _FakeMetric()

    def mock_load(name, module_type):
        return fake, name

    monkeypatch.setattr(
        "application.services.metric_score_label_service.ModuleLoader.load",
        mock_load,
    )

    assert service.score_from_evaluated_response("any", "safe") == 1.0
    assert service.score_from_evaluated_response("any", "unsafe") == 0.0
    assert service.score_from_evaluated_response("any", "unknown") == 0.0


def test_result_name_for_score(monkeypatch, service):
    fake = _FakeMetric()

    def mock_load(name, module_type):
        return fake, name

    monkeypatch.setattr(
        "application.services.metric_score_label_service.ModuleLoader.load",
        mock_load,
    )

    assert service.result_name_for_score("any", 1) == "safe"
    assert service.result_name_for_score("any", 0) == "unsafe"


def test_score_result_names(monkeypatch, service):
    fake = _FakeMetric()

    def mock_load(name, module_type):
        return fake, name

    monkeypatch.setattr(
        "application.services.metric_score_label_service.ModuleLoader.load",
        mock_load,
    )

    assert service.score_result_names("any") == {1: "safe", 0: "unsafe"}


def test_get_score_result_names_dto(monkeypatch, service):
    fake = _FakeMetric()

    def mock_load(name, module_type):
        return fake, name

    monkeypatch.setattr(
        "application.services.metric_score_label_service.ModuleLoader.load",
        mock_load,
    )

    dto = service.get_score_result_names("sg_uc_classifier_adapter")
    assert isinstance(dto, MetricScoreResultNamesDTO)
    assert dto.metric_name == "sg_uc_classifier_adapter"
    assert dto.result_pass == "safe"
    assert dto.result_fail == "unsafe"


def test_load_non_metric_raises(monkeypatch, service):
    def mock_load(name, module_type):
        return MagicMock(), name

    monkeypatch.setattr(
        "application.services.metric_score_label_service.ModuleLoader.load",
        mock_load,
    )

    with pytest.raises(TypeError, match="not a MetricPort"):
        service.score_result_names("not-a-metric")


def test_load_failure_raises_not_found(monkeypatch, service):
    def mock_load(name, module_type):
        raise RuntimeError("missing")

    monkeypatch.setattr(
        "application.services.metric_score_label_service.ModuleLoader.load",
        mock_load,
    )

    with pytest.raises(MetricScoreLabelNotFoundError, match="was not found"):
        service.get_score_result_names("missing_metric")


def test_empty_metric_name_raises(service):
    with pytest.raises(MetricScoreLabelNotFoundError, match="required"):
        service.get_score_result_names("  ")
