"""Unit tests for BenchmarkRunPromptRegenerationService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.dto.run_bundle_dto import BenchmarkRunTestPromptResponseDTO
from application.services.benchmark_run_prompt_regeneration_service import (
    BenchmarkRunPromptNotFoundError,
    BenchmarkRunPromptRegenerationConflictError,
    BenchmarkRunPromptRegenerationService,
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
    return BenchmarkRunPromptRegenerationService()


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
        prompt_additional_info="How do I ...?",
        prediction_result="old response",
        evaluation_prediction_result=str(
            {"score": 0, "evaluated_response": "Disagree"}
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
async def test_regenerate_conflict_when_prompt_running(
    mock_prompt_repo_class,
    mock_status_repo_class,
    mock_run_service_class,
    service,
):
    entity = _prompt(status="running")
    mock_prompt_repo = MagicMock()
    mock_prompt_repo.get_by_id.return_value = entity
    mock_prompt_repo.get_all_by_run_test_id.return_value = [entity]
    mock_prompt_repo_class.return_value = mock_prompt_repo
    mock_status_repo_class.return_value.get_by_id.return_value = _status()
    mock_run_service_class.return_value.get_run_by_id.return_value = _run()

    with pytest.raises(
        BenchmarkRunPromptRegenerationConflictError, match="this prompt"
    ):
        await service.regenerate(42)
