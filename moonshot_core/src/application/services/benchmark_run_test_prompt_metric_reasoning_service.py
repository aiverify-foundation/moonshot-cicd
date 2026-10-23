"""
Persist metric reasoning for a benchmark run test prompt.

Constructs the repository only when a non-empty reason will be inserted,
so a metric with no reasoning does not open a database session.
"""

from typing import Any, Optional

from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_metric_reasoning_adapter import (
    SqlAlchemyBenchmarkRunTestPromptMetricReasoningRepository,
)
from application.ports.benchmark_run_test_prompt_metric_reasoning_repository import (
    BenchmarkRunTestPromptMetricReasoningRepository,
)
from domain.entities.benchmark_run_test_prompt_metric_reasoning_entity import (
    BenchmarkRunTestPromptMetricReasoningEntity,
)


class BenchmarkRunTestPromptMetricReasoningService:
    """
    Save a metric result's ``reason`` onto benchmark_run_test_prompt_metric_reasoning.

    Rows are append-only. A rejudge inserts a new row; the current reasoning
    is the row with the highest id.
    """

    def __init__(
        self,
        repository: Optional[BenchmarkRunTestPromptMetricReasoningRepository] = None,
    ):
        self._repository = repository

    def save_if_present(
        self,
        benchmark_run_test_prompt_id: int,
        evaluated_result: Any,
    ) -> Optional[BenchmarkRunTestPromptMetricReasoningEntity]:
        """
        Insert ``evaluated_result["reason"]`` when it is a non-empty string.

        Args:
            benchmark_run_test_prompt_id: benchmark_run_test_prompt.id.
            evaluated_result: Metric result dict, or anything else the
                processor stored. Non-dicts and blank reasons are ignored.

        Returns:
            The saved entity, or None when no row is stored.
        """
        reason = self._reason_to_store(evaluated_result)
        if reason is None:
            return None
        repository = self._repository
        if repository is None:
            repository = SqlAlchemyBenchmarkRunTestPromptMetricReasoningRepository()
        return repository.add_metric_reasoning(benchmark_run_test_prompt_id, reason)

    @staticmethod
    def _reason_to_store(evaluated_result: Any) -> Optional[str]:
        """Return the original reason string, or None when nothing should be stored."""
        if not isinstance(evaluated_result, dict):
            return None
        reason = evaluated_result.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            return None
        return reason
