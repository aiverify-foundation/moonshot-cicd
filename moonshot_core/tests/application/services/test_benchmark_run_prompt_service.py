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


class TestPatchUserFeedback:
    """Tests for patch_user_feedback."""

    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestPromptRepository"
    )
    def test_invalid_user_evaluation_raises(self, mock_prompt_repo_class, service):
        mock_prompt_repo_class.return_value = MagicMock()
        with pytest.raises(ValueError, match="user_evaluation"):
            service.patch_user_feedback(2, 99, "x")

    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestPromptRepository"
    )
    def test_not_found_returns_none(self, mock_prompt_repo_class, service):
        mock_prompt_repo = MagicMock()
        mock_prompt_repo.get_by_id.return_value = None
        mock_prompt_repo_class.return_value = mock_prompt_repo

        assert service.patch_user_feedback(2, 1, "note") is None
        mock_prompt_repo.update.assert_not_called()

    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestPromptRepository"
    )
    def test_updates_repository(self, mock_prompt_repo_class, service):
        entity = BenchmarkRunTestPromptEntity(
            id=5,
            run_test_id=10,
            prompt_id=1,
            status="completed",
            target="t",
        )
        mock_prompt_repo = MagicMock()
        mock_prompt_repo.get_by_id.return_value = entity

        def capture_update(e):
            return e

        mock_prompt_repo.update.side_effect = capture_update
        mock_prompt_repo_class.return_value = mock_prompt_repo

        out = service.patch_user_feedback(5, 0, "  note  ")

        assert out is not None
        assert out.user_evaluation == 0
        assert out.user_notes == "note"
        mock_prompt_repo.get_by_id.assert_called_once_with(5)
        mock_prompt_repo.update.assert_called_once()

    @patch(
        "application.services.benchmark_run_prompt_service."
        "SqlAlchemyBenchmarkRunTestPromptRepository"
    )
    def test_clears_notes_when_empty_string(self, mock_prompt_repo_class, service):
        entity = BenchmarkRunTestPromptEntity(
            id=5,
            run_test_id=10,
            prompt_id=1,
            status="completed",
            target="t",
            user_notes="old",
        )
        mock_prompt_repo = MagicMock()
        mock_prompt_repo.get_by_id.return_value = entity
        mock_prompt_repo.update.side_effect = lambda e: e
        mock_prompt_repo_class.return_value = mock_prompt_repo

        out = service.patch_user_feedback(5, 1, "   ")
        assert out.user_notes is None
