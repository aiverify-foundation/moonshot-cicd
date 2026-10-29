"""Unit tests for SharedConfigSeedService (adapter mocked)."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from application.services.shared_config_seed_service import SharedConfigSeedService


@pytest.fixture
def mock_adapter():
    return MagicMock()


@pytest.fixture
def service(mock_adapter):
    return SharedConfigSeedService(adapter=mock_adapter)


class TestSharedConfigSeedService:
    """Unit tests for seed_from_data with mocked adapter."""

    def test_seed_from_data_calls_get_or_create_metric_for_each_metric_name(
        self, service, mock_adapter
    ):
        mock_adapter.get_or_create_metric.return_value = 1
        mock_adapter.get_bundle_id.return_value = None
        mock_adapter.insert_bundle.return_value = 1
        mock_adapter.get_dataset_id_by_system_name_latest.return_value = 42
        mock_adapter.get_test_id.return_value = None
        mock_adapter.insert_test.return_value = 10
        mock_adapter.grouping_exists.return_value = False

        data = {
            "bundle-a": {
                "name": "Bundle A",
                "tests": [
                    {
                        "name": "Test 1",
                        "dataset": "some-dataset",
                        "metric": {"name": "refusal_adapter"},
                    },
                ],
            },
        }
        service.seed_from_data(data)

        mock_adapter.get_or_create_metric.assert_any_call("refusal_adapter")
        assert mock_adapter.get_or_create_metric.call_count >= 1

    def test_seed_from_data_uses_get_dataset_id_by_system_name_latest(
        self, service, mock_adapter
    ):
        mock_adapter.get_or_create_metric.return_value = 1
        mock_adapter.get_bundle_id.return_value = None
        mock_adapter.insert_bundle.return_value = 1
        mock_adapter.get_dataset_id_by_system_name_latest.return_value = 42
        mock_adapter.get_test_id.return_value = None
        mock_adapter.insert_test.return_value = 10
        mock_adapter.grouping_exists.return_value = False

        data = {
            "bundle-x": {
                "name": "Bundle X",
                "tests": [
                    {
                        "name": "Only Test",
                        "dataset": "mlc-ailuminate-hte",
                        "metric": {"name": "acc"},
                    },
                ],
            },
        }
        service.seed_from_data(data)

        mock_adapter.get_dataset_id_by_system_name_latest.assert_called_once_with(
            "mlc-ailuminate-hte"
        )
        mock_adapter.insert_test.assert_called_once()
        call_kw = mock_adapter.insert_test.call_args[1]
        assert call_kw["dataset_id"] == 42

    def test_seed_from_data_creates_bundle_and_test_and_grouping(
        self, service, mock_adapter
    ):
        mock_adapter.get_or_create_metric.return_value = 1
        mock_adapter.get_bundle_id.return_value = None
        mock_adapter.insert_bundle.return_value = 1
        mock_adapter.get_dataset_id_by_system_name_latest.return_value = 42
        mock_adapter.get_test_id.side_effect = [None, None]
        mock_adapter.insert_test.side_effect = [10, 11]
        mock_adapter.grouping_exists.return_value = False

        data = {
            "bundle-two": {
                "name": "Bundle Two",
                "tests": [
                    {"name": "Test A", "dataset": "ds1", "metric": {"name": "m1"}},
                    {"name": "Test B", "dataset": "ds1", "metric": {"name": "m1"}},
                ],
            },
        }
        service.seed_from_data(data)

        assert mock_adapter.get_bundle_id.call_count == 1
        assert mock_adapter.insert_bundle.call_count == 1
        assert mock_adapter.insert_test.call_count == 2
        assert mock_adapter.insert_grouping.call_count == 2
        mock_adapter.get_bundle_id.assert_called_once_with(1, "bundle-two")
        call_bundle = mock_adapter.insert_bundle.call_args[1]
        assert call_bundle["system_name"] == "bundle-two"
        assert call_bundle["visible"] is True
        assert mock_adapter.grouping_exists.call_count == 2

    def test_seed_from_data_passes_visible_false(self, service, mock_adapter):
        mock_adapter.get_or_create_metric.return_value = 1
        mock_adapter.get_bundle_id.return_value = None
        mock_adapter.insert_bundle.return_value = 1
        mock_adapter.get_dataset_id_by_system_name_latest.return_value = 42
        mock_adapter.get_test_id.return_value = None
        mock_adapter.insert_test.return_value = 10
        mock_adapter.grouping_exists.return_value = False

        data = {
            "hidden-bundle": {
                "name": "Hidden",
                "visible": False,
                "tests": [
                    {"name": "T", "dataset": "ds1", "metric": {"name": "m1"}},
                ],
            },
        }
        service.seed_from_data(data)

        assert mock_adapter.insert_bundle.call_args[1]["visible"] is False

    def test_seed_from_data_updates_existing_bundle(self, service, mock_adapter):
        mock_adapter.get_or_create_metric.return_value = 1
        mock_adapter.get_bundle_id.return_value = 99
        mock_adapter.get_dataset_id_by_system_name_latest.return_value = 42
        mock_adapter.get_test_id.return_value = None
        mock_adapter.insert_test.return_value = 10
        mock_adapter.grouping_exists.return_value = False

        data = {
            "bundle-x": {
                "name": "Renamed",
                "visible": False,
                "tests": [
                    {"name": "T", "dataset": "ds1", "metric": {"name": "m1"}},
                ],
            },
        }
        service.seed_from_data(data)

        mock_adapter.insert_bundle.assert_not_called()
        mock_adapter.update_bundle.assert_called_once_with(
            99,
            name="Renamed",
            description=None,
            category="",
            visible=False,
        )

    def test_seed_from_data_logs_duplicate_names_but_still_seeds(
        self, service, mock_adapter, tmp_path, monkeypatch
    ):
        log_path = tmp_path / "startup_config_warnings.log"
        monkeypatch.setenv("MS_STARTUP_CONFIG_WARNINGS_LOG_PATH", str(log_path))
        mock_adapter.get_or_create_metric.return_value = 1
        mock_adapter.get_bundle_id.return_value = None
        mock_adapter.insert_bundle.side_effect = [1, 2]
        mock_adapter.get_dataset_id_by_system_name_latest.return_value = 42
        mock_adapter.get_test_id.return_value = None
        mock_adapter.insert_test.side_effect = [10, 11]
        mock_adapter.grouping_exists.return_value = False

        data = {
            "bundle-one": {
                "name": "One",
                "tests": [
                    {"name": "Same Name", "dataset": "ds1", "metric": {"name": "m1"}},
                ],
            },
            "bundle-two": {
                "name": "Two",
                "tests": [
                    {"name": "Same Name", "dataset": "ds1", "metric": {"name": "m1"}},
                ],
            },
        }
        service.seed_from_data(data, config_path=Path("/cfg/shared.yaml"))

        assert mock_adapter.insert_test.call_count == 2
        log_text = log_path.read_text(encoding="utf-8")
        payload = json.loads(log_text.split("=" * 72 + "\n")[1].strip())
        assert payload["issue"] == "duplicate_test_display_name"
        assert payload["test_name"] == "Same Name"
        assert payload["config_source"] == "/cfg/shared.yaml"
