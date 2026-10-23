"""Unit tests for BenchmarkRunTestPromptMetricReasoningService."""

from unittest.mock import MagicMock, patch

from application.services.benchmark_run_test_prompt_metric_reasoning_service import (
    BenchmarkRunTestPromptMetricReasoningService,
)
from domain.entities.benchmark_run_test_prompt_metric_reasoning_entity import (
    BenchmarkRunTestPromptMetricReasoningEntity,
)


def _saved_entity(reasoning: str) -> BenchmarkRunTestPromptMetricReasoningEntity:
    return BenchmarkRunTestPromptMetricReasoningEntity(
        id=1,
        benchmark_run_test_prompt_id=10,
        reasoning=reasoning,
    )


class TestSaveIfPresent:
    """save_if_present inserts only a non-empty reason string."""

    def test_inserts_original_reason_string(self):
        """A non-empty reason is passed through unchanged."""
        repository = MagicMock()
        repository.add_metric_reasoning.return_value = _saved_entity(
            "  within tolerance  "
        )
        service = BenchmarkRunTestPromptMetricReasoningService(repository=repository)

        saved = service.save_if_present(
            10,
            {"score": 1.0, "reason": "  within tolerance  "},
        )

        repository.add_metric_reasoning.assert_called_once_with(
            10, "  within tolerance  "
        )
        assert saved is repository.add_metric_reasoning.return_value

    @patch(
        "application.services.benchmark_run_test_prompt_metric_reasoning_service."
        "SqlAlchemyBenchmarkRunTestPromptMetricReasoningRepository"
    )
    def test_skips_missing_blank_and_non_dict_results(self, mock_repo_class):
        """No repository is constructed when there is nothing to store."""
        service = BenchmarkRunTestPromptMetricReasoningService()

        assert service.save_if_present(10, {"score": 1.0}) is None
        assert service.save_if_present(10, {"reason": ""}) is None
        assert service.save_if_present(10, {"reason": "   "}) is None
        assert service.save_if_present(10, {"reason": None}) is None
        assert service.save_if_present(10, {"reason": 1}) is None
        assert service.save_if_present(10, None) is None
        assert service.save_if_present(10, "within tolerance") is None

        mock_repo_class.assert_not_called()
