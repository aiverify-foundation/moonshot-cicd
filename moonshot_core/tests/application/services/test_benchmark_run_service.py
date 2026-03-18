"""Unit tests for BenchmarkRunService."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from application.services.benchmark_run_service import BenchmarkRunService
from domain.entities.benchmark_run_entity import BenchmarkRunEntity


@pytest.fixture
def service():
    return BenchmarkRunService()


class TestGetAllRuns:
    """Tests for get_all_runs."""

    @patch(
        "application.services.benchmark_run_service.SqlAlchemyBenchmarkRunRepository"
    )
    def test_returns_empty_when_no_runs(self, mock_repo_class, service):
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = []
        mock_repo_class.return_value = mock_repo

        result = service.get_all_runs()

        assert result == []
        mock_repo.get_all.assert_called_once()

    @patch(
        "application.services.benchmark_run_service.SqlAlchemyBenchmarkRunRepository"
    )
    def test_returns_all_entities(self, mock_repo_class, service):
        t = datetime.now(timezone.utc)
        runs = [
            BenchmarkRunEntity(
                id=1,
                name="run-a",
                status="running",
                endpoint_type="LLM_Provider",
                start_time=t,
            ),
            BenchmarkRunEntity(
                id=2,
                name="run-b",
                status="completed",
                endpoint_type="LLM_Provider",
                start_time=t,
                end_time=t,
            ),
        ]
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = runs
        mock_repo_class.return_value = mock_repo

        result = service.get_all_runs()

        assert result == runs
        mock_repo.get_all.assert_called_once()
