"""Derive LLM-as-judge (AAJ) metadata from benchmark metric configuration."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.services.app_config import AppConfig

# Metric adapter module name (YAML metric.name / DB benchmark_test_metric.name).
LLAMAGUARD_ANNOTATOR_METRIC = "llamaguardannotator_adapter"
REFUSAL_METRIC = "refusal_adapter"
CYBERSEC_REFUSAL_METRIC = "cybersecevalannotator2_adapter"
# Connector system names used by moonshot_config for each metric's evaluator.
LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME = "together_adapter"
REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME = "openai_adapter"

_METRIC_AAJ_PROVIDER_BY_NAME: dict[str, str] = {
    LLAMAGUARD_ANNOTATOR_METRIC: LLAMAGUARD_JUDGE_CONNECTOR_SYSTEM_NAME,
    REFUSAL_METRIC: REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME,
    CYBERSEC_REFUSAL_METRIC: REFUSAL_JUDGE_CONNECTOR_SYSTEM_NAME,
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


def metric_grader_model_name(
    metric: dict[str, Any] | None,
    *,
    app_config: AppConfig | None = None,
) -> str | None:
    """
    Return the evaluator model configured in moonshot_config for this metric.

    Reads ``metrics[].connector_configurations.model`` for the metric adapter name.
    Returns ``None`` when the metric is missing, unknown, or has no model configured.
    """
    if not metric:
        return None
    name = metric.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    if app_config is None:
        from domain.services.app_config import AppConfig

        app_config = AppConfig()
    config = app_config.get_metric_config(name.strip())
    if config is None:
        return None
    model = (config.connector_configurations.model or "").strip()
    return model if model else None
