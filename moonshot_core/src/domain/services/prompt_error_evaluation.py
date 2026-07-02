"""Helpers for per-prompt benchmark failures (score 0, synthetic metric entities)."""

from __future__ import annotations

from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.prompt_entity import PromptEntity
from domain.services.enums.task_manager_status import TaskManagerStatus

FAILED_EVALUATED_RESULT: dict = {"score": 0}


def mean_entity_score(entities: list[MetricIndividualEntity]) -> float:
    """Mean per-prompt score (0–1); missing evaluated_result counts as 0."""
    if not entities:
        return 0.0
    total = sum(
        (entity.evaluated_result or {}).get("score", 0) for entity in entities
    )
    return total / len(entities)


def synthetic_error_entity(prompt: PromptEntity) -> MetricIndividualEntity:
    """Build a MetricIndividualEntity for a failed prompt (aggregation score 0)."""
    return MetricIndividualEntity(
        prompt=prompt.prompt,
        predicted_result=ConnectorResponseEntity(response="", context=[]),
        target=prompt.target,
        reference_context=prompt.reference_context,
        evaluated_result=dict(FAILED_EVALUATED_RESULT),
    )


def entities_for_aggregation(
    processed_prompts: list[PromptEntity],
) -> list[MetricIndividualEntity]:
    """Map processed prompts to metric entities, using score 0 for ERROR state."""
    entities: list[MetricIndividualEntity] = []
    for prompt in processed_prompts:
        if prompt.evaluation_result is not None:
            entities.append(prompt.evaluation_result)
        elif prompt.state == TaskManagerStatus.ERROR:
            entities.append(synthetic_error_entity(prompt))
    return entities
