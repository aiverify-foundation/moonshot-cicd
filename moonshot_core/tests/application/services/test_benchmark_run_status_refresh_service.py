"""Unit tests for BenchmarkRunStatusRefreshService."""

from unittest.mock import MagicMock, patch

from application.services.benchmark_run_status_refresh_service import (
    BenchmarkRunStatusRefreshService,
)
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)


def _prompt(
    *,
    prompt_id: int = 42,
    run_test_id: int = 7,
    status: str = "completed",
) -> BenchmarkRunTestPromptEntity:
    return BenchmarkRunTestPromptEntity(
        id=prompt_id,
        run_test_id=run_test_id,
        prompt_id=3,
        status=status,
        target="safe",
    )


def _status(
    *,
    status_id: int = 7,
    run_id: int = 1,
    test_id: int = 99,
    status: str = "completed",
) -> BenchmarkRunTestStatusEntity:
    return BenchmarkRunTestStatusEntity(
        id=status_id,
        run_id=run_id,
        test_id=test_id,
        status=status,
    )


def _run(*, status: str = "completed") -> BenchmarkRunEntity:
    return BenchmarkRunEntity(
        id=1,
        name="run-1",
        status=status,
        endpoint_type="LLM_Provider",
        llm_provider_id=10,
        llm_provider_model_id=20,
        llm_provider_model_config_id=30,
    )


@patch(
    "application.services.benchmark_run_status_refresh_service." "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "BenchmarkRunTestStatusService"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
def test_refresh_last_error_prompt_marks_test_and_run_completed(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_status_service_class,
    mock_run_service_class,
):
    """Last errored prompt succeeding → test completed, run completed."""
    completed = _prompt(status="completed")
    status_entity = _status(status="completed_with_errors")

    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_all_by_run_test_id.return_value = [completed]
    mock_prompt_repo_class.return_value = mock_prompt_repo

    mock_status_repo = MagicMock()
    mock_status_repo.get_by_id.return_value = status_entity
    mock_status_repo.get_all_by_run_id.return_value = [status_entity]
    mock_status_repo_class.return_value = mock_status_repo

    mock_run_service = MagicMock()
    mock_run_service.get_run_by_id.return_value = _run(status="failed")
    mock_run_service_class.return_value = mock_run_service

    BenchmarkRunStatusRefreshService().refresh_after_prompt_update(7)

    updated_test = (
        mock_status_service_class.return_value.update_run_test_status.call_args[0][0]
    )
    assert updated_test.status == "completed"
    updated_run = mock_run_service.update_run.call_args[0][0]
    assert updated_run.status == "completed"
    assert updated_run.end_time is not None


@patch(
    "application.services.benchmark_run_status_refresh_service." "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "BenchmarkRunTestStatusService"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
def test_refresh_keeps_completed_with_errors_when_sibling_still_errors(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_status_service_class,
    mock_run_service_class,
):
    """Sibling still error → test stays completed_with_errors, run stays failed."""
    completed = _prompt(prompt_id=42, status="completed")
    sibling_error = _prompt(prompt_id=43, status="error")
    status_entity = _status(status="completed_with_errors")

    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_all_by_run_test_id.return_value = [completed, sibling_error]
    mock_prompt_repo_class.return_value = mock_prompt_repo

    mock_status_repo = MagicMock()
    mock_status_repo.get_by_id.return_value = status_entity
    mock_status_repo.get_all_by_run_id.return_value = [status_entity]
    mock_status_repo_class.return_value = mock_status_repo

    mock_run_service = MagicMock()
    mock_run_service.get_run_by_id.return_value = _run(status="failed")
    mock_run_service_class.return_value = mock_run_service

    BenchmarkRunStatusRefreshService().refresh_after_prompt_update(7)

    updated_test = (
        mock_status_service_class.return_value.update_run_test_status.call_args[0][0]
    )
    assert updated_test.status == "completed_with_errors"
    mock_run_service.update_run.assert_not_called()


@patch(
    "application.services.benchmark_run_status_refresh_service." "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "BenchmarkRunTestStatusService"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_status_refresh_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
def test_refresh_skips_when_run_test_missing(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_status_service_class,
    mock_run_service_class,
):
    mock_status_repo_class.return_value.get_by_id.return_value = None

    BenchmarkRunStatusRefreshService().refresh_after_prompt_update(99)

    mock_status_service_class.return_value.update_run_test_status.assert_not_called()
    mock_run_service_class.return_value.update_run.assert_not_called()
