"""Unit tests for BenchmarkRunPromptRegenerationService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.dto.run_bundle_dto import BenchmarkRunTestPromptResponseDTO
from application.services.benchmark_run_prompt_regeneration_service import (
    BenchmarkRunPromptNotFoundError,
    BenchmarkRunPromptRegenerationConflictError,
    BenchmarkRunPromptRegenerationService,
    _RUNNING_EVALUATION_RESULT,
)
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)
from domain.entities.connector_entity import ConnectorEntity


@pytest.fixture
def service():
    BenchmarkRunPromptRegenerationService.clear_bulk_jobs_for_tests()
    yield BenchmarkRunPromptRegenerationService()
    BenchmarkRunPromptRegenerationService.clear_bulk_jobs_for_tests()


def _prompt(
    *,
    prompt_id: int = 42,
    run_test_id: int = 7,
    status: str = "completed",
    evaluated_response: str = "Disagree",
) -> BenchmarkRunTestPromptEntity:
    return BenchmarkRunTestPromptEntity(
        id=prompt_id,
        run_test_id=run_test_id,
        prompt_id=3,
        status=status,
        target="safe",
        prompt_additional_info="How do I ...?",
        prediction_result="old response",
        evaluation_prediction_result=str(
            {"score": 0, "evaluated_response": evaluated_response}
        ),
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


@pytest.mark.asyncio
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunResultsQueryService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "AsyncioPromptProcessor"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "DatabaseConnectorConfigService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkTestConfigAdapter"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
async def test_regenerate_success_updates_and_returns_dto(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    mock_test_config_class,
    mock_connector_service_class,
    mock_processor_class,
    mock_query_service_class,
    service,
):
    entity = _prompt()
    updated = _prompt()
    updated.prediction_result = "new response"
    updated.evaluation_prediction_result = str(
        {"score": 1, "evaluated_response": "Agree"}
    )
    status_entity = _status()

    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_by_id.side_effect = [entity, updated]
    mock_prompt_repo.get_all_by_run_test_id.return_value = [entity]
    mock_prompt_repo.update.side_effect = lambda e: e
    mock_prompt_repo_class.return_value = mock_prompt_repo

    mock_status_repo = MagicMock()
    mock_status_repo.get_by_id.return_value = status_entity
    mock_status_repo_class.return_value = mock_status_repo

    mock_run_service_class.return_value.get_run_by_id.return_value = _run()
    mock_test_config_class.return_value.get_test_info.return_value = (
        "Safety",
        "ds",
        "ailuminate_safety_classifier_adapter",
    )
    connector = MagicMock(spec=ConnectorEntity)
    mock_connector_service_class.return_value.build_connector_entity.return_value = (
        connector
    )

    mock_processor = MagicMock()
    mock_processor.process_prompts = AsyncMock(return_value=([], {}))
    mock_processor_class.return_value = mock_processor

    dto = BenchmarkRunTestPromptResponseDTO(
        id=42,
        run_test_id=7,
        prompt_id=3,
        status="completed",
        target="safe",
        prediction_result="new response",
        evaluation_prediction_result=str({"score": 1, "evaluated_response": "Agree"}),
        test_name="Safety",
        test_id=99,
        metric_name="ailuminate_safety_classifier_adapter",
    )
    mock_query_service_class.return_value.prompt_dto_for_entity.return_value = dto

    result = await service.regenerate(42)

    assert result is dto
    assert result.score == 1.0
    assert entity.status == "running"
    assert entity.prediction_result is None
    assert entity.evaluation_prediction_result == _RUNNING_EVALUATION_RESULT
    assert entity.evaluation_accuracy == 0.0
    mock_processor.process_prompts.assert_awaited_once()
    call_kwargs = mock_processor.process_prompts.await_args
    assert call_kwargs.kwargs["write_to_db"] is True
    assert call_kwargs.kwargs["run_test_id"] == 7
    assert call_kwargs.args[2] == {"name": "ailuminate_safety_classifier_adapter"}
    mock_query_service_class.return_value.prompt_dto_for_entity.assert_called_once_with(
        1, updated
    )


@pytest.mark.asyncio
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
async def test_regenerate_not_found(
    mock_prompt_repo_class, mock_status_repo_class, service
):
    mock_prompt_repo_class.return_value.get_by_id.return_value = None
    with pytest.raises(BenchmarkRunPromptNotFoundError, match="prompt_id=99"):
        await service.regenerate(99)
    mock_status_repo_class.return_value.get_by_id.assert_not_called()


@pytest.mark.asyncio
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
async def test_regenerate_conflict_when_run_active(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    service,
):
    entity = _prompt()
    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_by_id.return_value = entity
    mock_prompt_repo.get_all_by_run_test_id.return_value = [entity]
    mock_prompt_repo_class.return_value = mock_prompt_repo
    mock_status_repo_class.return_value.get_by_id.return_value = _status()
    mock_run_service_class.return_value.get_run_by_id.return_value = _run(
        status="running"
    )

    with pytest.raises(
        BenchmarkRunPromptRegenerationConflictError, match="still running"
    ):
        await service.regenerate(42)


@pytest.mark.asyncio
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunResultsQueryService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "AsyncioPromptProcessor"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "DatabaseConnectorConfigService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkTestConfigAdapter"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
async def test_regenerate_allows_when_target_prompt_already_running(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    mock_test_config_class,
    mock_connector_service_class,
    mock_processor_class,
    mock_query_service_class,
    service,
):
    entity = _prompt(status="running")
    updated = _prompt(status="completed")
    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_by_id.side_effect = [entity, updated]
    mock_prompt_repo.get_all_by_run_test_id.return_value = [entity]
    mock_prompt_repo.update.side_effect = lambda e: e
    mock_prompt_repo_class.return_value = mock_prompt_repo
    mock_status_repo_class.return_value.get_by_id.return_value = _status()
    mock_run_service_class.return_value.get_run_by_id.return_value = _run()
    mock_test_config_class.return_value.get_test_info.return_value = (
        "Safety",
        "ds",
        "ailuminate_safety_classifier_adapter",
    )
    mock_connector_service_class.return_value.build_connector_entity.return_value = (
        MagicMock(spec=ConnectorEntity)
    )
    mock_processor = MagicMock()
    mock_processor.process_prompts = AsyncMock(return_value=([], {}))
    mock_processor_class.return_value = mock_processor
    mock_query_service_class.return_value.prompt_dto_for_entity.return_value = (
        BenchmarkRunTestPromptResponseDTO(
            id=42,
            run_test_id=7,
            prompt_id=3,
            status="completed",
            target="safe",
            test_name="Safety",
            test_id=99,
        )
    )

    result = await service.regenerate(42)

    assert result.status == "completed"
    assert entity.evaluation_prediction_result == _RUNNING_EVALUATION_RESULT
    assert entity.evaluation_accuracy == 0.0
    mock_processor.process_prompts.assert_awaited_once()


@pytest.mark.asyncio
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
async def test_regenerate_conflict_when_sibling_prompt_running(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    service,
):
    entity = _prompt(prompt_id=42, status="error")
    sibling = _prompt(prompt_id=43, status="running")
    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_by_id.return_value = entity
    mock_prompt_repo.get_all_by_run_test_id.return_value = [entity, sibling]
    mock_prompt_repo_class.return_value = mock_prompt_repo
    mock_status_repo_class.return_value.get_by_id.return_value = _status()
    mock_run_service_class.return_value.get_run_by_id.return_value = _run()

    with pytest.raises(
        BenchmarkRunPromptRegenerationConflictError, match="another prompt"
    ):
        await service.regenerate(42)


@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunPromptService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
def test_prepare_regenerate_failed_marks_run_and_prompts_running(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    mock_prompt_service_class,
    service,
):
    errored_a = _prompt(prompt_id=1, run_test_id=7, status="error")
    errored_b = _prompt(prompt_id=2, run_test_id=8, status="error")
    completed = _prompt(prompt_id=3, run_test_id=7, status="completed")
    mock_prompt_service_class.return_value.get_all_prompts_by_run_id.return_value = [
        errored_a,
        errored_b,
        completed,
    ]

    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_all_by_run_test_id.side_effect = lambda rtid: (
        [errored_a, completed] if rtid == 7 else [errored_b]
    )
    mock_prompt_repo.update.side_effect = lambda e: e
    mock_prompt_repo_class.return_value = mock_prompt_repo

    mock_status_repo_class.return_value.get_all_by_run_id.return_value = [
        _status(status_id=7, test_id=99, status="completed_with_errors"),
        _status(status_id=8, test_id=100, status="failed"),
    ]

    run = _run(status="completed")
    mock_run_service = MagicMock()
    mock_run_service.get_run_by_id.return_value = run
    mock_run_service.update_run.side_effect = lambda e: e
    mock_run_service_class.return_value = mock_run_service

    result = service.prepare_regenerate_failed_for_run(1)

    assert result.total == 2
    assert result.prompt_ids == [1, 2]
    assert result.run_test_ids == [7, 8]
    assert run.status == "completed"
    assert errored_a.status == "running"
    assert errored_b.status == "running"
    assert errored_a.prediction_result is None
    assert errored_b.prediction_result is None
    assert errored_a.evaluation_prediction_result == _RUNNING_EVALUATION_RESULT
    assert errored_b.evaluation_prediction_result == _RUNNING_EVALUATION_RESULT
    assert errored_a.evaluation_accuracy == 0.0
    assert errored_b.evaluation_accuracy == 0.0
    assert completed.status == "completed"
    assert completed.prediction_result == "old response"
    mock_run_service.update_run.assert_not_called()
    progress = service.get_regenerate_failed_progress(1)
    assert progress.status == "in_progress"
    assert progress.total == 2


@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunPromptService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
def test_prepare_regenerate_failed_empty_does_not_flip_run(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    mock_prompt_service_class,
    service,
):
    mock_prompt_service_class.return_value.get_all_prompts_by_run_id.return_value = [
        _prompt(status="completed")
    ]
    run = _run(status="completed")
    mock_run_service = MagicMock()
    mock_run_service.get_run_by_id.return_value = run
    mock_run_service_class.return_value = mock_run_service

    result = service.prepare_regenerate_failed_for_run(1)

    assert result.total == 0
    assert result.prompt_ids == []
    assert run.status == "completed"
    mock_run_service.update_run.assert_not_called()


@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunPromptService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
def test_prepare_regenerate_failed_includes_unknown_evaluation(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    mock_prompt_service_class,
    service,
):
    unknown = _prompt(
        prompt_id=1, run_test_id=7, status="completed", evaluated_response="unknown"
    )
    completed = _prompt(
        prompt_id=2, run_test_id=7, status="completed", evaluated_response="safe"
    )
    errored = _prompt(prompt_id=3, run_test_id=8, status="error")
    mock_prompt_service_class.return_value.get_all_prompts_by_run_id.return_value = [
        unknown,
        completed,
        errored,
    ]

    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_all_by_run_test_id.side_effect = lambda rtid: (
        [unknown, completed] if rtid == 7 else [errored]
    )
    mock_prompt_repo.update.side_effect = lambda e: e
    mock_prompt_repo_class.return_value = mock_prompt_repo

    mock_status_repo_class.return_value.get_all_by_run_id.return_value = [
        _status(status_id=7, test_id=99, status="completed"),
        _status(status_id=8, test_id=100, status="completed_with_errors"),
    ]

    run = _run(status="completed")
    mock_run_service = MagicMock()
    mock_run_service.get_run_by_id.return_value = run
    mock_run_service_class.return_value = mock_run_service

    result = service.prepare_regenerate_failed_for_run(1)

    assert result.total == 2
    assert result.prompt_ids == [1, 3]
    assert result.run_test_ids == [7, 8]
    assert unknown.status == "running"
    assert unknown.prediction_result is None
    assert unknown.evaluation_prediction_result == _RUNNING_EVALUATION_RESULT
    assert unknown.evaluation_accuracy == 0.0
    assert completed.status == "completed"
    assert completed.prediction_result == "old response"
    assert errored.status == "running"
    assert errored.evaluation_prediction_result == _RUNNING_EVALUATION_RESULT


def test_evaluated_response_is_unknown_accepts_bare_and_dict_blobs(service):
    assert service._evaluated_response_is_unknown("unknown")
    assert service._evaluated_response_is_unknown(
        str({"score": 0.0, "evaluated_response": "unknown"})
    )
    assert service._evaluated_response_is_unknown(
        '{"score": 0, "evaluated_response": "Unknown"}'
    )
    assert not service._evaluated_response_is_unknown(
        str({"score": 1.0, "evaluated_response": "safe"})
    )
    assert not service._evaluated_response_is_unknown(None)


@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunPromptService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
def test_prepare_regenerate_failed_conflict_when_run_active(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    mock_prompt_service_class,
    service,
):
    mock_run_service_class.return_value.get_run_by_id.return_value = _run(
        status="running"
    )
    with pytest.raises(
        BenchmarkRunPromptRegenerationConflictError, match="still running"
    ):
        service.prepare_regenerate_failed_for_run(1)
    mock_prompt_service_class.return_value.get_all_prompts_by_run_id.assert_not_called()


@pytest.mark.asyncio
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunStatusRefreshService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "AsyncioPromptProcessor"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "DatabaseConnectorConfigService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkTestConfigAdapter"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunPromptService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "BenchmarkRunService"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestStatusRepository"
)
@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
async def test_regenerate_failed_for_run_groups_and_refreshes_once(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    mock_prompt_service_class,
    mock_test_config_class,
    mock_connector_service_class,
    mock_processor_class,
    mock_refresh_class,
    service,
):
    a = _prompt(prompt_id=1, run_test_id=7, status="running")
    b = _prompt(prompt_id=2, run_test_id=7, status="running")
    c = _prompt(prompt_id=3, run_test_id=8, status="running")

    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_by_id.side_effect = lambda pid: {1: a, 2: b, 3: c}.get(pid)
    mock_prompt_repo_class.return_value = mock_prompt_repo

    mock_status_repo = MagicMock()
    mock_status_repo.get_by_id.side_effect = lambda rtid: (
        _status(status_id=rtid, test_id=90 + rtid, status="completed_with_errors")
    )
    mock_status_repo_class.return_value = mock_status_repo

    run = _run(status="completed")
    mock_run_service = MagicMock()
    mock_run_service.get_run_by_id.return_value = run
    mock_run_service_class.return_value = mock_run_service

    mock_test_config_class.return_value.get_test_info.return_value = (
        "Safety",
        "ds",
        "ailuminate_safety_classifier_adapter",
    )
    mock_connector_service_class.return_value.build_connector_entity.return_value = (
        MagicMock(spec=ConnectorEntity)
    )
    mock_processor = MagicMock()
    mock_processor.process_prompts = AsyncMock(return_value=([], {}))
    mock_processor_class.return_value = mock_processor

    # Register a job so progress status can flip to completed.
    from application.services.benchmark_run_prompt_regeneration_service import (
        BulkRegenerateJobState,
        _bulk_regen_jobs,
    )

    _bulk_regen_jobs[1] = BulkRegenerateJobState(
        prompt_ids=[1, 2, 3], total=3, status="in_progress"
    )

    await service.regenerate_failed_for_run(1, [1, 2, 3])

    assert mock_processor.process_prompts.await_count == 2
    mock_refresh_class.return_value.refresh_after_bulk_prompt_updates.assert_called_once_with(
        1, [7, 8]
    )
    assert service.get_regenerate_failed_progress(1).status == "completed"


def test_get_regenerate_failed_progress_idle(service):
    progress = service.get_regenerate_failed_progress(99)
    assert progress.status == "idle"
    assert progress.total == 0
    assert progress.done == 0
    assert progress.failed == 0


@patch(
    "application.services.benchmark_run_prompt_regeneration_service."
    "SqlAlchemyBenchmarkRunTestPromptRepository"
)
def test_get_regenerate_failed_progress_counts_done(
    mock_prompt_repo_class, service
):
    from application.services.benchmark_run_prompt_regeneration_service import (
        BulkRegenerateJobState,
        _bulk_regen_jobs,
    )

    running = _prompt(prompt_id=1, status="running")
    completed = _prompt(prompt_id=2, status="completed")
    errored = _prompt(prompt_id=3, status="error")
    mock_prompt_repo_class.return_value.get_by_id.side_effect = lambda pid: {
        1: running,
        2: completed,
        3: errored,
    }.get(pid)
    _bulk_regen_jobs[5] = BulkRegenerateJobState(
        prompt_ids=[1, 2, 3], total=3, status="in_progress"
    )

    progress = service.get_regenerate_failed_progress(5)
    assert progress.status == "in_progress"
    assert progress.total == 3
    assert progress.done == 2
    assert progress.failed == 1
