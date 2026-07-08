"""Tests for BenchmarkRunResultsQueryService error enrichment."""

from unittest.mock import MagicMock, patch

from application.dto.run_bundle_dto import BenchmarkRunTestPromptResponseDTO
from application.services.benchmark_run_results_query_service import (
    BenchmarkRunResultsQueryService,
)
from domain.entities.benchmark_run_test_error_entity import (
    BenchmarkRunTestErrorEntity,
)
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)


@patch(
    "application.services.benchmark_run_results_query_service.SqlAlchemyBenchmarkRunTestErrorRepository"
)
@patch(
    "application.services.benchmark_run_results_query_service.BenchmarkRunPromptService"
)
def test_list_prompt_dtos_enriches_latest_error_fields(
    mock_prompt_service_class,
    mock_error_repo_class,
):
    entity = BenchmarkRunTestPromptEntity(
        id=42,
        run_test_id=7,
        prompt_id=3,
        status="error",
        evaluation_prediction_result=str({"score": 0}),
    )
    mock_prompt_service_class.return_value.get_all_prompts_by_run_id.return_value = [
        entity
    ]

    mock_error_repo = MagicMock()
    mock_error_repo_class.return_value = mock_error_repo
    mock_error_repo.get_latest_by_prompt_ids.return_value = {
        42: BenchmarkRunTestErrorEntity(
            id=1,
            benchmark_run_test_prompt_id=42,
            error_message="connector timeout",
            error_source="connector",
        )
    }

    service = BenchmarkRunResultsQueryService()
    with patch.object(
        service,
        "_run_test_enrichment_maps",
        return_value=({7: "Safety"}, {7: 99}),
    ):
        dtos = service.list_prompt_dtos(run_id=1)

    assert len(dtos) == 1
    dto = dtos[0]
    assert isinstance(dto, BenchmarkRunTestPromptResponseDTO)
    assert dto.error_message == "connector timeout"
    assert dto.error_source == "connector"
    assert dto.test_name == "Safety"
    assert dto.test_id == 99
    mock_error_repo.get_latest_by_prompt_ids.assert_called_once_with([42])
