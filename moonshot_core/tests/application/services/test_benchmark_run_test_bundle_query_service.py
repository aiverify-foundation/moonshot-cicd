"""Unit tests for BenchmarkRunTestBundleQueryService."""

from unittest.mock import MagicMock, patch

from domain.entities.benchmark_run_test_bundle_entity import (
    BenchmarkRunTestBundleEntity,
)


@patch(
    "application.services.benchmark_run_test_bundle_query_service."
    "SqlAlchemyBenchmarkRunTestBundleRepository"
)
def test_get_all_by_run_id_delegates_to_repository(mock_repo_class):
    from application.services.benchmark_run_test_bundle_query_service import (
        BenchmarkRunTestBundleQueryService,
    )

    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    entities = [
        BenchmarkRunTestBundleEntity(
            id=1, run_id=3, test_bundle_id=9, test_id=50
        ),
    ]
    mock_repo.get_all_by_run_id.return_value = entities

    svc = BenchmarkRunTestBundleQueryService()
    result = svc.get_all_by_run_id(3)

    assert result == entities
    mock_repo_class.assert_called_once_with()
    mock_repo.get_all_by_run_id.assert_called_once_with(3)
