"""Unit tests for BenchmarkRunTestBundlePopulationService."""

from unittest.mock import MagicMock

import pytest

from application.services.benchmark_run_test_bundle_population_service import (
    BenchmarkRunTestBundlePopulationService,
)
from domain.entities.benchmark_run_test_bundle_entity import (
    BenchmarkRunTestBundleEntity,
)


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_config():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_config):
    return BenchmarkRunTestBundlePopulationService(
        run_test_bundle_repository=mock_repo,
        config_adapter=mock_config,
    )


class TestInsertRunTestBundle:
    """Tests for insert_run_test_bundle."""

    def test_builds_entity_and_calls_repo_save(self, service, mock_repo):
        """Service builds entity and calls repository.save; does not call entity.save."""
        saved = BenchmarkRunTestBundleEntity(
            id=1,
            run_id=10,
            test_bundle_id=20,
            test_id=30,
        )
        mock_repo.save.return_value = saved

        result = service.insert_run_test_bundle(
            run_id=10,
            test_bundle_id=20,
            test_id=30,
        )

        assert result == saved
        mock_repo.save.assert_called_once()
        call_entity = mock_repo.save.call_args[0][0]
        assert call_entity.id is None
        assert call_entity.run_id == 10
        assert call_entity.test_bundle_id == 20
        assert call_entity.test_id == 30


class TestPopulateRunBundle:
    """Tests for populate_run_bundle."""

    def test_resolves_bundle_gets_test_ids_inserts_each(self, service, mock_repo, mock_config):
        """Calls config for bundle id and test ids, then insert_run_test_bundle per test."""
        mock_config.get_bundle_id_by_system_name_latest.return_value = 5
        mock_config.get_test_ids_by_bundle_id.return_value = [101, 102]
        mock_repo.save.return_value = BenchmarkRunTestBundleEntity(
            id=1, run_id=1, test_bundle_id=5, test_id=101
        )

        result = service.populate_run_bundle(run_id=1, test_bundle_system_name="my-bundle")

        assert result["run_id"] == 1
        assert result["test_bundle_id"] == 5
        assert result["inserted_count"] == 2
        mock_config.get_bundle_id_by_system_name_latest.assert_called_once_with("my-bundle")
        mock_config.get_test_ids_by_bundle_id.assert_called_once_with(5)
        assert mock_repo.save.call_count == 2
        calls = [mock_repo.save.call_args_list[i][0][0] for i in range(2)]
        assert calls[0].test_id == 101 and calls[1].test_id == 102

    def test_returns_zero_inserted_when_bundle_has_no_tests(
        self, service, mock_repo, mock_config
    ):
        """When bundle has no groupings, inserted_count is 0."""
        mock_config.get_bundle_id_by_system_name_latest.return_value = 3
        mock_config.get_test_ids_by_bundle_id.return_value = []

        result = service.populate_run_bundle(run_id=1, test_bundle_system_name="empty-bundle")

        assert result["run_id"] == 1
        assert result["test_bundle_id"] == 3
        assert result["inserted_count"] == 0
        mock_repo.save.assert_not_called()

    def test_raises_value_error_when_bundle_not_found(self, service, mock_config):
        """Propagates ValueError when config raises (bundle not found)."""
        mock_config.get_bundle_id_by_system_name_latest.side_effect = ValueError(
            "Bundle not found: system_name='missing'."
        )

        with pytest.raises(ValueError, match="Bundle not found"):
            service.populate_run_bundle(run_id=1, test_bundle_system_name="missing")
