"""Unit tests for SharedConfigSeedService.seed_if_test_file_changed (all dependencies mocked)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from application.services.shared_config_seed_service import (
    SharedConfigSeedService,
    TEST_FILE_LAST_MODIFIED_KEY,
    SHARED_CONFIG_SEED_VERSION_KEY,
)
from domain.entities.moonshot_config_entity import MoonshotConfigEntity


@pytest.fixture
def config_path():
    return Path("/fake/data/test_configs/shared.yaml")


@pytest.fixture
def moonshot_config_mock():
    return MagicMock()


@pytest.fixture
def shared_config_repo_mock():
    return MagicMock()


@pytest.fixture
def dataset_seed_service_mock():
    return MagicMock()


@pytest.fixture
def mock_adapter():
    return MagicMock()


@pytest.fixture
def service(
    mock_adapter,
    moonshot_config_mock,
    shared_config_repo_mock,
    dataset_seed_service_mock,
):
    return SharedConfigSeedService(
        adapter=mock_adapter,
        moonshot_config_repository=moonshot_config_mock,
        shared_config_repository=shared_config_repo_mock,
        benchmark_dataset_seed_service=dataset_seed_service_mock,
    )


class TestSharedConfigSeedServiceSeedIfTestFileChanged:
    """Unit tests for seed_if_test_file_changed."""

    def test_raises_when_optional_deps_missing(self, mock_adapter):
        service_no_deps = SharedConfigSeedService(adapter=mock_adapter)
        with pytest.raises(ValueError) as exc_info:
            service_no_deps.seed_if_test_file_changed()
        assert "seed_if_test_file_changed requires" in str(exc_info.value)

    def test_returns_false_when_config_file_not_found(
        self, service, shared_config_repo_mock, config_path
    ):
        shared_config_repo_mock.get_last_modified.side_effect = FileNotFoundError()
        result = service.seed_if_test_file_changed(config_path=config_path)
        assert result is False
        service._dataset_seed_service.seed_benchmark_dataset.assert_not_called()
        service._moonshot_config.set.assert_not_called()

    def test_returns_false_when_file_unchanged(
        self,
        service,
        moonshot_config_mock,
        shared_config_repo_mock,
        config_path,
    ):
        shared_config_repo_mock.get_last_modified.return_value = 100.0
        moonshot_config_mock.get_by_key.return_value = MoonshotConfigEntity(
            id=1, key=TEST_FILE_LAST_MODIFIED_KEY, value="150"
        )
        result = service.seed_if_test_file_changed(config_path=config_path)
        assert result is False
        service._dataset_seed_service.seed_benchmark_dataset.assert_not_called()
        service._moonshot_config.set.assert_not_called()
        moonshot_config_mock.get_by_key.assert_called_once_with(
            TEST_FILE_LAST_MODIFIED_KEY
        )

    def test_returns_true_and_seeds_when_first_run(
        self,
        service,
        moonshot_config_mock,
        shared_config_repo_mock,
        dataset_seed_service_mock,
        config_path,
    ):
        moonshot_config_mock.get_by_key.return_value = None
        shared_config_repo_mock.get_last_modified.return_value = 200.0
        minimal_config = {
            "bundle-a": {
                "name": "Bundle A",
                "tests": [
                    {"name": "Test 1", "dataset": "foo", "metric": {"name": "acc"}},
                ],
            },
        }
        shared_config_repo_mock.get_config.return_value = minimal_config
        service._seed_from_data = MagicMock()

        result = service.seed_if_test_file_changed(config_path=config_path, version=1)

        assert result is True
        dataset_seed_service_mock.seed_benchmark_dataset.assert_called_once_with("foo")
        service._seed_from_data.assert_called_once_with(
            minimal_config, config_path, 1
        )
        assert moonshot_config_mock.set.call_count == 2
        moonshot_config_mock.set.assert_any_call(
            TEST_FILE_LAST_MODIFIED_KEY, "200.0"
        )
        moonshot_config_mock.set.assert_any_call(
            SHARED_CONFIG_SEED_VERSION_KEY, "1"
        )

    def test_returns_true_when_stored_less_than_mtime(
        self,
        service,
        moonshot_config_mock,
        shared_config_repo_mock,
        dataset_seed_service_mock,
        config_path,
    ):
        moonshot_config_mock.get_by_key.side_effect = [
            MoonshotConfigEntity(
                id=1, key=TEST_FILE_LAST_MODIFIED_KEY, value="50"
            ),
            MoonshotConfigEntity(
                id=2, key=SHARED_CONFIG_SEED_VERSION_KEY, value="50"
            ),
        ]
        shared_config_repo_mock.get_last_modified.return_value = 100.0
        minimal_config = {"b": {"tests": [{"dataset": "ds1", "metric": {"name": "m1"}}]}}
        shared_config_repo_mock.get_config.return_value = minimal_config
        service._seed_from_data = MagicMock()

        result = service.seed_if_test_file_changed(config_path=config_path)

        assert result is True
        dataset_seed_service_mock.seed_benchmark_dataset.assert_called_once_with(
            "ds1"
        )
        service._seed_from_data.assert_called_once()
        call_args = service._seed_from_data.call_args[0]
        assert call_args[0] == minimal_config
        assert call_args[1] == config_path
        assert call_args[2] == 51
        assert moonshot_config_mock.set.call_count == 2
        moonshot_config_mock.set.assert_any_call(
            TEST_FILE_LAST_MODIFIED_KEY, "100.0"
        )
        moonshot_config_mock.set.assert_any_call(
            SHARED_CONFIG_SEED_VERSION_KEY, "51"
        )

    def test_collects_all_dataset_names_from_config(
        self,
        service,
        moonshot_config_mock,
        shared_config_repo_mock,
        dataset_seed_service_mock,
        config_path,
    ):
        moonshot_config_mock.get_by_key.return_value = None
        shared_config_repo_mock.get_last_modified.return_value = 300.0
        config_with_duplicates = {
            "bundle-1": {
                "tests": [
                    {"name": "T1", "dataset": "aaa", "metric": {"name": "m1"}},
                    {"name": "T2", "dataset": "bbb", "metric": {"name": "m1"}},
                ],
            },
            "bundle-2": {
                "tests": [
                    {"name": "T3", "dataset": "aaa", "metric": {"name": "m1"}},
                ],
            },
        }
        shared_config_repo_mock.get_config.return_value = config_with_duplicates
        service._seed_from_data = MagicMock()

        result = service.seed_if_test_file_changed(config_path=config_path)

        assert result is True
        assert dataset_seed_service_mock.seed_benchmark_dataset.call_count == 2
        calls = [
            dataset_seed_service_mock.seed_benchmark_dataset.call_args_list[0][0][0],
            dataset_seed_service_mock.seed_benchmark_dataset.call_args_list[1][0][0],
        ]
        assert calls == ["aaa", "bbb"]
