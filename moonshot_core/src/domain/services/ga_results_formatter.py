"""
Shared helpers for GA Schema1 benchmark result JSON (file export and DB reconstruction).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from application.dto.run_bundle_dto import parse_evaluation_prediction_result
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.prompt_entity import PromptEntity
from domain.services.app_config import AppConfig
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader

SECRET_PARAM_KEYS = frozenset(
    {
        "api_key",
        "api_key_auth_custom_header",
        "secret",
        "token",
        "password",
        "authorization",
    }
)


def metric_categorise_result(metric_name: str) -> bool:
    """Return whether the metric groups individual_results by evaluated_response."""
    _, metric_id = ModuleLoader.load(metric_name, ModuleTypes.METRIC)
    metric_config = AppConfig().get_metric_config(metric_id)
    if metric_config is None:
        raise ValueError(f"Metric config not found for metric_id={metric_id}")
    return bool(metric_config.params.get("categorise_result"))


def redact_connector_params(params: dict[str, Any]) -> dict[str, Any]:
    """Remove secret-like keys from connector params for API export."""
    redacted: dict[str, Any] = {}
    for key, value in params.items():
        if key.lower() in SECRET_PARAM_KEYS:
            redacted[key] = ""
        else:
            redacted[key] = value
    return redacted


def format_metadata(
    test_name: str,
    dataset: str,
    metric: dict,
    connector_entity: ConnectorEntity,
    task_type: str,
    *,
    redact_secrets: bool = False,
) -> dict:
    """Format per-test metadata for GA Schema1 run_results[].metadata."""
    params = connector_entity.params or {}
    if redact_secrets:
        params = redact_connector_params(params)

    formatted_metadata: dict[str, Any] = {
        "test_name": test_name,
        "dataset": dataset,
        "metric": metric,
        "type": task_type,
        "connector": {
            "connector_adapter": connector_entity.connector_adapter,
            "model": connector_entity.model,
            "model_endpoint": connector_entity.model_endpoint,
            "params": params,
            "connector_pre_prompt": connector_entity.connector_pre_prompt,
            "connector_post_prompt": connector_entity.connector_post_prompt,
            "system_prompt": connector_entity.system_prompt,
        },
    }
    if task_type == "scan":
        del formatted_metadata["dataset"]
    return formatted_metadata


def format_run_metadata(
    run_name: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    """Build top-level run_metadata; test_id equals run_id (run name)."""
    duration = (end_time - start_time).total_seconds()
    time_fmt = "%Y-%m-%d %H:%M:%S"
    return {
        "run_id": run_name,
        "test_id": run_name,
        "start_time": start_time.strftime(time_fmt),
        "end_time": end_time.strftime(time_fmt),
        "duration": duration,
    }


def add_timing_to_metadata(
    metadata: dict,
    start_time: Optional[datetime],
    end_time: Optional[datetime],
) -> dict:
    """Attach start_time, end_time, duration to per-test metadata."""
    if start_time is None or end_time is None:
        metadata.update({"start_time": "", "end_time": "", "duration": 0.0})
        return metadata
    duration = (end_time - start_time).total_seconds()
    time_fmt = "%Y-%m-%d %H:%M:%S"
    metadata.update(
        {
            "start_time": start_time.strftime(time_fmt),
            "end_time": end_time.strftime(time_fmt),
            "duration": duration,
        }
    )
    return metadata


def prompt_entity_to_ga_dict(prompt_entity: PromptEntity) -> dict:
    """Convert a PromptEntity to a GA Schema1 individual prompt dict."""
    evaluation = prompt_entity.evaluation_result
    return {
        "prompt_id": prompt_entity.index,
        "prompt": evaluation.prompt,
        "predicted_result": {
            "response": evaluation.predicted_result.response,
            "context": evaluation.predicted_result.context,
        },
        "target": evaluation.target,
        "evaluated_result": evaluation.evaluated_result,
        "prompt_additional_info": prompt_entity.additional_info,
        "state": prompt_entity.state.value,
    }


def benchmark_run_prompt_to_ga_dict(
    row: BenchmarkRunTestPromptEntity,
) -> dict:
    """Convert a DB prompt row to a GA Schema1 individual prompt dict."""
    evaluated = parse_evaluation_prediction_result(row.evaluation_prediction_result)
    if not isinstance(evaluated, dict):
        evaluated = {}

    prompt_text = evaluated.get("prompt") or row.prompt_additional_info or ""
    predicted_response = evaluated.get("predicted_value") or row.prediction_result or ""

    context: list[Any] = []
    if row.prediction_context:
        try:
            parsed_ctx = json.loads(row.prediction_context)
            if isinstance(parsed_ctx, list):
                context = parsed_ctx
        except json.JSONDecodeError:
            context = []

    return {
        "prompt_id": row.prompt_id,
        "prompt": prompt_text,
        "predicted_result": {
            "response": predicted_response,
            "context": context,
        },
        "target": row.target,
        "evaluated_result": evaluated,
        "prompt_additional_info": {},
        "state": row.status,
    }


def categorise_prompt_dicts(
    prompt_dicts: list[dict], metric_name: str
) -> dict[str, list[dict]]:
    """Group prompt dicts into GA individual_results (categorised or all_results)."""
    if not metric_categorise_result(metric_name):
        return {"all_results": prompt_dicts}

    categorised: dict[str, list[dict]] = {}
    for prompt_dict in prompt_dicts:
        evaluated = prompt_dict.get("evaluated_result") or {}
        if not isinstance(evaluated, dict):
            evaluated = {}
        category = evaluated.get("evaluated_response", "unknown")
        categorised.setdefault(str(category), []).append(prompt_dict)

    return {key: categorised[key] for key in sorted(categorised)}


def convert_prompt_entities_to_dicts(
    prompt_entities: list[PromptEntity], metric: dict
) -> dict:
    """Convert PromptEntity list to GA individual_results (TaskManager-compatible)."""
    prompt_dicts = [prompt_entity_to_ga_dict(entity) for entity in prompt_entities]
    return categorise_prompt_dicts(prompt_dicts, metric["name"])
