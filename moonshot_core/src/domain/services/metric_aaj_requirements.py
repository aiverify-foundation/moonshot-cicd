"""Derive LLM-as-judge (AAJ) metadata from benchmark metric configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from domain.services.logger import configure_logger

if TYPE_CHECKING:
    from domain.services.app_config import AppConfig

logger = configure_logger(__name__)

# Metric adapter module name (YAML metric.name / DB benchmark_test_metric.name).
# Membership means the metric can show an LLM-judge connector. Which connector
# is shown comes only from moonshot_config connector_adapter.
AILUMINATE_SAFETY_CLASSIFIER_METRIC = "ailuminate_safety_classifier_adapter"
SG_UC_CLASSIFIER_METRIC = "sg_uc_classifier_adapter"
SG_FACT_CHECK_METRIC = "sg_fact_check_adapter"
REFUSAL_METRIC = "refusal_adapter"
CYBERSEC_REFUSAL_METRIC = "cybersecevalannotator2_adapter"
CONTRADICTION_JUDGE_APPROX5_METRIC = "contradiction_judge_approx5_adapter"

_AAJ_METRIC_NAMES: frozenset[str] = frozenset(
    {
        AILUMINATE_SAFETY_CLASSIFIER_METRIC,
        SG_UC_CLASSIFIER_METRIC,
        SG_FACT_CHECK_METRIC,
        REFUSAL_METRIC,
        CYBERSEC_REFUSAL_METRIC,
        CONTRADICTION_JUDGE_APPROX5_METRIC,
    }
)


def _connector_adapter_from_config(
    metric_name: str,
    *,
    app_config: AppConfig | None,
) -> str | None:
    """Return metrics[].connector_configurations.connector_adapter when set."""
    if app_config is None:
        from domain.services.app_config import AppConfig

        app_config = AppConfig()
    config = app_config.get_metric_config(metric_name)
    if config is None:
        return None
    adapter = (config.connector_configurations.connector_adapter or "").strip()
    return adapter if adapter else None


def metric_aaj_fields(
    metric: dict[str, Any] | None,
    *,
    app_config: AppConfig | None = None,
) -> tuple[bool, str | None]:
    """
    Return (requires_llm_aaj, metric_provider_system_name) for API/DTO enrichment.

    A metric is an LLM judge only when its adapter name is in the hardcoded
    whitelist. ``metric_provider_system_name`` is that metric's
    ``connector_adapter`` from moonshot_config. When the metric is whitelisted
    but the adapter is missing or blank, the judge connector is hidden.
    """
    if not metric:
        return False, None
    name = metric.get("name")
    if not isinstance(name, str) or not name.strip():
        return False, None
    metric_name = name.strip()
    if metric_name not in _AAJ_METRIC_NAMES:
        return False, None
    from_config = _connector_adapter_from_config(metric_name, app_config=app_config)
    if from_config is None:
        logger.warning(
            "LLM-as-judge metric %s has no connector_adapter in config; "
            "hiding the judge connector",
            metric_name,
        )
        return False, None
    return True, from_config


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
