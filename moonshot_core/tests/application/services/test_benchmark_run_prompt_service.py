"""Unit tests for BenchmarkRunPromptService."""

from unittest.mock import MagicMock, patch

import pytest

from application.services.benchmark_run_prompt_service import (
    BenchmarkRunPromptService,
)
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)


@pytest.fixture
def service():
    return BenchmarkRunPromptService()


class TestGetAllPromptsByRunId:
    """Tests for get_all_prompts_by_run_id."""

    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestPromptRepository"
    )
    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestStatusRepository"
    )
    def test_returns_all_prompts_from_multiple_run_tests(
        self, mock_status_repo_class, mock_prompt_repo_class, service
    ):
        """Given run_id with two run-tests and prompts each, returns flattened list."""
        status1 = BenchmarkRunTestStatusEntity(
            id=100,
            run_id=10,
            test_id=20,
            status="completed",
        )
        status2 = BenchmarkRunTestStatusEntity(
            id=101,
            run_id=10,
            test_id=21,
            status="completed",
        )
        mock_status_repo = MagicMock()
        mock_status_repo.get_all_by_run_id.return_value = [status1, status2]
        mock_status_repo_class.return_value = mock_status_repo

        prompts1 = [
            BenchmarkRunTestPromptEntity(
                id=1,
                run_test_id=100,
                prompt_id=1,
                status="completed",
                target="4",
            ),
        ]
        prompts2 = [
            BenchmarkRunTestPromptEntity(
                id=2,
                run_test_id=101,
                prompt_id=1,
                status="completed",
                target="yes",
            ),
        ]
        mock_prompt_repo = MagicMock()
        mock_prompt_repo.get_all_by_run_test_id.side_effect = [
            prompts1,
            prompts2,
        ]
        mock_prompt_repo_class.return_value = mock_prompt_repo

        result = service.get_all_prompts_by_run_id(10)

        assert len(result) == 2
        assert result[0].id == 1 and result[0].run_test_id == 100
        assert result[1].id == 2 and result[1].run_test_id == 101
        mock_status_repo.get_all_by_run_id.assert_called_once_with(10)
        assert mock_prompt_repo.get_all_by_run_test_id.call_count == 2
        mock_prompt_repo.get_all_by_run_test_id.assert_any_call(100)
        mock_prompt_repo.get_all_by_run_test_id.assert_any_call(101)

    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestPromptRepository"
    )
    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestStatusRepository"
    )
    def test_returns_empty_list_when_run_has_no_statuses(
        self, mock_status_repo_class, mock_prompt_repo_class, service
    ):
        """When run_id has no run-test statuses, returns empty list."""
        mock_status_repo = MagicMock()
        mock_status_repo.get_all_by_run_id.return_value = []
        mock_status_repo_class.return_value = mock_status_repo

        result = service.get_all_prompts_by_run_id(99)

        assert result == []
        mock_status_repo.get_all_by_run_id.assert_called_once_with(99)
        mock_prompt_repo_class.return_value.get_all_by_run_test_id.assert_not_called()

    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestPromptRepository"
    )
    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestStatusRepository"
    )
    def test_returns_empty_list_when_statuses_have_no_prompts(
        self, mock_status_repo_class, mock_prompt_repo_class, service
    ):
        """When run has statuses but no prompts, returns empty list."""
        status = BenchmarkRunTestStatusEntity(
            id=100,
            run_id=10,
            test_id=20,
            status="not_started",
        )
        mock_status_repo = MagicMock()
        mock_status_repo.get_all_by_run_id.return_value = [status]
        mock_status_repo_class.return_value = mock_status_repo

        mock_prompt_repo = MagicMock()
        mock_prompt_repo.get_all_by_run_test_id.return_value = []
        mock_prompt_repo_class.return_value = mock_prompt_repo

        result = service.get_all_prompts_by_run_id(10)

        assert result == []
        mock_prompt_repo.get_all_by_run_test_id.assert_called_once_with(100)
