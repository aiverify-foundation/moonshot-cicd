from abc import ABC, abstractmethod

from domain.entities.benchmark_run_test_prompt_metric_reasoning_entity import (
    BenchmarkRunTestPromptMetricReasoningEntity,
)


class BenchmarkRunTestPromptMetricReasoningRepository(ABC):
    """
    Abstract repository for benchmark_run_test_prompt_metric_reasoning rows.

    Storage is append-only. The current reasoning for a prompt is the row
    with the highest id. No row is stored when the metric produces no reasoning.
    """

    @abstractmethod
    def add_metric_reasoning(
        self, benchmark_run_test_prompt_id: int, reasoning: str
    ) -> BenchmarkRunTestPromptMetricReasoningEntity:
        """
        Insert a new metric-reasoning row. Never updates an existing row.

        Args:
            benchmark_run_test_prompt_id: benchmark_run_test_prompt.id.
            reasoning: Non-empty metric reasoning. None, empty, and
                whitespace-only values raise ValueError.

        Returns:
            Saved entity with id and create_dt populated.
        """
        pass

    @abstractmethod
    def get_latest_metric_reasoning(
        self, benchmark_run_test_prompt_id: int
    ) -> BenchmarkRunTestPromptMetricReasoningEntity | None:
        """
        Return the highest-id reasoning row for one prompt, or None.
        """
        pass

    @abstractmethod
    def get_latest_metric_reasoning_for_prompts(
        self, prompt_ids: list[int]
    ) -> dict[int, BenchmarkRunTestPromptMetricReasoningEntity]:
        """
        Return the highest-id reasoning row per prompt id.

        Args:
            prompt_ids: benchmark_run_test_prompt.id values to look up.

        Returns:
            Map of prompt id -> latest reasoning entity. Omits prompts with
            no reasoning. An empty list returns an empty dict.
        """
        pass
