"""Derive LLM-as-judge (AAJ) metadata from benchmark metric configuration."""

from __future__ import annotations

from typing import Any

# Metric adapter module name (YAML metric.name / DB benchmark_test_metric.name).
LLAMAGUARD_ANNOTATOR_METRIC = "llamaguardannotator_adapter"
# Connector system name used by moonshot_config for that metric's evaluator.
LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME = "together_adapter"


def metric_aaj_fields(metric: dict[str, Any] | None) -> tuple[bool, str | None]:
    """
    Return (requires_llm_aaj, metric_provider_system_name) for API/DTO enrichment.

    ``metric_provider_system_name`` is the metric-side connector ``system_name``
    (same notion as ``connector_adapter`` in moonshot_config metrics).
    """
    if not metric:
        return False, None
    name = metric.get("name")
    if name == LLAMAGUARD_ANNOTATOR_METRIC:
        return True, LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME
    return False, None
