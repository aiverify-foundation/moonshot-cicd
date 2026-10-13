"""Unit tests for BenchmarkRunResumeService."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from application.services.benchmark_run_resume_service import (
    BenchmarkRunResumeBadRequestError,
    BenchmarkRunResumeConflictError,
    BenchmarkRunResumeNotFoundError,
    BenchmarkRunResumeService,
)
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)


def _run(
    *,
    run_id: int = 12,
    status: str = "failed",
    llm: bool = True,
) -> BenchmarkRunEntity:
    return BenchmarkRunEntity(
        id=run_id,
        name="run-12",
        status=status,
        endpoint_type="LLM_Provider" if llm else "Custom_App",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        llm_provider_id=10 if llm else None,
        llm_provider_model_id=20 if llm else None,
        llm_provider_model_config_id=30 if llm else None,
        custom_app_id=None if llm else 1,
        custom_app_config_id=None if llm else 2,
    )


def _status(
    *,
    status_id: int = 7,
    run_id: int = 12,
    test_id: int = 99,
    status: str = "in_progress",
) -> BenchmarkRunTestStatusEntity:
    return BenchmarkRunTestStatusEntity(
        id=status_id,
        run_id=run_id,
        test_id=test_id,
        status=status,
        start_dt=datetime.now(timezone.utc),
        end_dt=None,
    )


def _prompt(
    *,
    prompt_id: int = 42,
    run_test_id: int = 7,
    status: str = "pending",
) -> BenchmarkRunTestPromptEntity:
    return BenchmarkRunTestPromptEntity(
        id=prompt_id,
        run_test_id=run_test_id,
        prompt_id=3,
        status=status,
        target="safe",
        prompt_additional_info="prompt text",
    )


@patch(
    "application.services.benchmark_run_resume_service.BenchmarkExecutionService"
)
@patch(
    "application.services.benchmark_run_resume_service.BenchmarkRunTestStatusService"
)
@patch(
    "application.services.benchmark_run_resume_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
@patch(
    "application.services.benchmark_run_resume_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch("application.services.benchmark_run_resume_service.BenchmarkRunService")
def test_resume_sets_running_resets_rows_and_spawns_bundles(
    mock_run_service_class,
    mock_status_repo_class,
    mock_prompt_repo_class,
    mock_status_service_class,
    mock_exec_class,
):
    run = _run(status="failed")
    status = _status(status="in_progress")
    stuck = _prompt(status="running")
    pending = _prompt(prompt_id=43, status="pending")

    mock_run_service_class.return_value.get_run_by_id.return_value = run
    mock_status_repo_class.return_value.get_all_by_run_id.return_value = [status]
    mock_prompt_repo_class.return_value.get_all_by_run_test_id.return_value = [
        stuck,
        pending,
    ]

    with patch.object(
        BenchmarkRunResumeService,
        "_load_bundles_with_incomplete_tests",
        return_value={"safety-bundle": {99}},
    ):
        result = BenchmarkRunResumeService().resume(12)

    assert result.run_id == 12
    assert result.resumed_test_count == 1
    assert "resume started" in result.message.lower()

    assert run.status == "running"
    assert run.end_time is None
    mock_run_service_class.return_value.update_run.assert_called_once_with(run)

    assert status.status == "not_started"
    assert status.end_dt is None
    mock_status_service_class.return_value.update_run_test_status.assert_called_once_with(
        status
    )

    assert stuck.status == "pending"
    mock_prompt_repo_class.return_value.update.assert_called_once_with(stuck)

    mock_exec_class.return_value.start_bundle_in_background.assert_called_once_with(
        "safety-bundle",
        12,
        llm_provider_id=10,
        llm_provider_model_id=20,
        llm_provider_model_config_id=30,
        custom_app_id=None,
        custom_app_config_id=None,
        test_ids=[99],
        continue_on_test_failure=True,
    )


@patch(
    "application.services.benchmark_run_resume_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
@patch(
    "application.services.benchmark_run_resume_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch("application.services.benchmark_run_resume_service.BenchmarkRunService")
def test_resume_not_found(
    mock_run_service_class, mock_status_repo_class, mock_prompt_repo_class
):
    mock_run_service_class.return_value.get_run_by_id.return_value = None
    with pytest.raises(BenchmarkRunResumeNotFoundError, match="id=99"):
        BenchmarkRunResumeService().resume(99)


@patch(
    "application.services.benchmark_run_resume_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
@patch(
    "application.services.benchmark_run_resume_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch("application.services.benchmark_run_resume_service.BenchmarkRunService")
def test_resume_conflict_when_nothing_incomplete(
    mock_run_service_class, mock_status_repo_class, mock_prompt_repo_class
):
    mock_run_service_class.return_value.get_run_by_id.return_value = _run(
        status="completed"
    )
    completed = _status(status="completed")
    mock_status_repo_class.return_value.get_all_by_run_id.return_value = [completed]
    mock_prompt_repo_class.return_value.get_all_by_run_test_id.return_value = [
        _prompt(status="completed")
    ]

    with pytest.raises(BenchmarkRunResumeConflictError, match="Nothing to resume"):
        BenchmarkRunResumeService().resume(12)


@patch("application.services.benchmark_run_resume_service.BenchmarkRunService")
def test_resume_bad_request_missing_connector(mock_run_service_class):
    run = BenchmarkRunEntity(
        id=12,
        name="run-12",
        status="running",
        endpoint_type="LLM_Provider",
    )
    mock_run_service_class.return_value.get_run_by_id.return_value = run
    with pytest.raises(BenchmarkRunResumeBadRequestError, match="connector"):
        BenchmarkRunResumeService().resume(12)


@patch(
    "application.services.benchmark_run_resume_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
@patch(
    "application.services.benchmark_run_resume_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch("application.services.benchmark_run_resume_service.BenchmarkRunService")
def test_resume_includes_terminal_test_with_pending_prompts(
    mock_run_service_class, mock_status_repo_class, mock_prompt_repo_class
):
    mock_run_service_class.return_value.get_run_by_id.return_value = _run(
        status="failed"
    )
    terminal = _status(status="failed")
    mock_status_repo_class.return_value.get_all_by_run_id.return_value = [terminal]
    mock_prompt_repo_class.return_value.get_all_by_run_test_id.return_value = [
        _prompt(status="pending"),
        _prompt(prompt_id=44, status="completed"),
    ]

    with patch.object(
        BenchmarkRunResumeService,
        "_load_bundles_with_incomplete_tests",
        return_value={"bundle-a": {99}},
    ), patch(
        "application.services.benchmark_run_resume_service.BenchmarkExecutionService"
    ) as mock_exec_class, patch(
        "application.services.benchmark_run_resume_service.BenchmarkRunTestStatusService"
    ):
        result = BenchmarkRunResumeService().resume(12)

    assert result.resumed_test_count == 1
    mock_exec_class.return_value.start_bundle_in_background.assert_called_once()
