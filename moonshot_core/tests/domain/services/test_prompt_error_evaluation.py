"""Tests for prompt error evaluation helpers."""

import pytest

from adapters.metric.accuracy_adapter import AccuracyAdapter
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.prompt_entity import PromptEntity
from domain.services.enums.task_manager_status import TaskManagerStatus
from domain.services.prompt_error_evaluation import (
    entities_for_aggregation,
    mean_entity_score,
    synthetic_error_entity,
)


def test_synthetic_error_entity_score_zero():
    prompt = PromptEntity(index=1, prompt="p", target="t")
    entity = synthetic_error_entity(prompt)
    assert entity.evaluated_result == {"score": 0}


def test_entities_for_aggregation_includes_error_as_score_zero():
    ok = PromptEntity(index=1, prompt="a", target="t")
    ok.evaluation_result = MetricIndividualEntity(
        prompt="a",
        predicted_result=ConnectorResponseEntity(response="r", context=[]),
        target="t",
        evaluated_result={"score": 1.0},
    )
    bad = PromptEntity(index=2, prompt="b", target="t")
    bad.state = TaskManagerStatus.ERROR

    entities = entities_for_aggregation([ok, bad])
    assert len(entities) == 2
    assert mean_entity_score(entities) == 0.5


@pytest.mark.asyncio
async def test_accuracy_get_results_counts_error_entity_as_zero():
    """Reverted accuracy aggregation: error entity lacks accuracy key → 2/3 rate."""
    entities = [
        MetricIndividualEntity(
            prompt="p1",
            predicted_result=ConnectorResponseEntity(response="a", context=[]),
            target="a",
            evaluated_result={"accuracy": True},
        ),
        MetricIndividualEntity(
            prompt="p2",
            predicted_result=ConnectorResponseEntity(response="b", context=[]),
            target="b",
            evaluated_result={"accuracy": True},
        ),
        synthetic_error_entity(PromptEntity(index=3, prompt="p3", target="t")),
    ]
    adapter = AccuracyAdapter.__new__(AccuracyAdapter)
    result = await adapter.get_results(entities)
    assert result["accuracy"]["exact_string_match"] == pytest.approx(200 / 3)
