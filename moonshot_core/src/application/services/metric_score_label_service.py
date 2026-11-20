"""Resolve binary scores and metric-owned result names for evaluated responses."""

from __future__ import annotations

from application.dto.metric_score_label_dto import MetricScoreResultNamesDTO
from domain.ports.metric_port import MetricPort
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

logger = configure_logger(__name__)


class MetricScoreLabelNotFoundError(ValueError):
    """Raised when a metric adapter cannot be loaded by name."""


class MetricScoreLabelService:
    """Load a metric adapter and expose its score ↔ result-name helpers."""

    def _load_metric(self, metric_name: str) -> MetricPort:
        name = (metric_name or "").strip()
        if not name:
            raise MetricScoreLabelNotFoundError("Metric name is required.")
        try:
            adapter_instance, _ = ModuleLoader.load(name, ModuleTypes.METRIC)
        except Exception as exc:
            logger.error("Failed to load metric '%s': %s", name, exc)
            raise MetricScoreLabelNotFoundError(
                f"Metric '{name}' was not found."
            ) from exc
        if not isinstance(adapter_instance, MetricPort):
            raise TypeError(
                f"Loaded module '{name}' is not a MetricPort "
                f"(got {type(adapter_instance)!r})"
            )
        return adapter_instance

    def score_from_evaluated_response(
        self, metric_name: str, evaluated_response: str
    ) -> float:
        """
        Return ``1.0`` or ``0.0`` for *evaluated_response* using the metric's
        pass/fail labels (unknown and non-pass labels map to ``0.0``).
        """
        metric = self._load_metric(metric_name)
        return metric.score_from_evaluated_response(evaluated_response)

    def result_name_for_score(self, metric_name: str, score: float | int) -> str:
        """Return the metric-owned result name for a binary score."""
        metric = self._load_metric(metric_name)
        return metric.result_name_for_score(score)

    def score_result_names(self, metric_name: str) -> dict[int, str]:
        """
        Return both poles for UI/export: ``{1: RESULT_PASS, 0: RESULT_FAIL}``.
        """
        metric = self._load_metric(metric_name)
        return {
            1: metric.RESULT_PASS,
            0: metric.RESULT_FAIL,
        }

    def get_score_result_names(self, metric_name: str) -> MetricScoreResultNamesDTO:
        """
        Return RESULT_PASS / RESULT_FAIL for *metric_name* (frontend-friendly).
        """
        name = (metric_name or "").strip()
        metric = self._load_metric(name)
        return MetricScoreResultNamesDTO(
            metric_name=name,
            result_pass=metric.RESULT_PASS,
            result_fail=metric.RESULT_FAIL,
        )
