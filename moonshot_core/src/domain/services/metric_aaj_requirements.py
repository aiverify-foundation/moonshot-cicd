"""Derive LLM-as-judge (AAJ) metadata from benchmark metric configuration."""

from __future__ import annotations

from typing import Any

# Metric adapter module name (YAML metric.name / DB benchmark_test_metric.name).
LLAMAGUARD_ANNOTATOR_METRIC = "llamaguardannotator_adapter"
REFUSAL_METRIC = "refusal_adapter"
# Connector system names used by moonshot_config for each metric's evaluator.
LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME = "together_adapter"
REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME = "openai_adapter"

_METRIC_AAJ_PROVIDER_BY_NAME: dict[str, str] = {
    LLAMAGUARD_ANNOTATOR_METRIC: LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME,
    REFUSAL_METRIC: REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME,
}


def metric_aaj_fields(metric: dict[str, Any] | None) -> tuple[bool, str | None]:
    """
    Return (requires_llm_aaj, metric_provider_system_name) for API/DTO enrichment.

    ``metric_provider_system_name`` is the metric-side connector ``system_name``
    (same notion as ``connector_adapter`` in moonshot_config metrics).
    """
    if not metric:
        return False, None
    name = metric.get("name")
    provider = _METRIC_AAJ_PROVIDER_BY_NAME.get(name)
    if provider is None:
        return False, None
    return True, provider
