import pytest
from unittest.mock import patch, MagicMock
from domain.services.loader.loader_types.config_loader import ConfigLoader
from domain.entities.app_config_entity import AppConfigEntity
from domain.ports.storage_provider_port import StorageProviderPort

@pytest.fixture
def storage_adapter():
    return MagicMock(spec=StorageProviderPort)

@pytest.fixture
def config_loader(storage_adapter):
    return ConfigLoader(storage_adapter)

@pytest.mark.parametrize("loader_name, file_content, deserialized_data, should_fail", [
    (
        "valid_config.yaml",
        "mock file content",
        {
            "common": {
                "max_concurrency": 10,
                "max_calls_per_minute": 100,
                "max_attempts": 5
            },
            "connectors_configurations": [
                {"type": "connector1", "config": {"key": "value"}}
            ],
            "metrics": [
                {"name": "metric1", "params": {"param1": "value1"}}
            ],
            "attack_modules": [
                {"name": "attack1", "params": {"param2": "value2"}}
            ]
        },
        False
    ),
    (
        "non_existent_file.yaml",
        None,
        None,
        True
    ),
    (
        "invalid_content.yaml",
        "invalid content",
        None,
        True
    ),
])
@patch('domain.services.loader.factory.file_format_factory.FileFormatFactory.get_adapter')
def test_load(mock_get_adapter, config_loader, loader_name, file_content, deserialized_data, should_fail):
    with patch('domain.services.loader.loader_types.config_loader.logger') as mock_logger:
        # Mock the storage adapter's behavior
        config_loader.storage_adapter.read_file.return_value = file_content

        # Mock the file format adapter
        mock_file_format_adapter = MagicMock()
        if deserialized_data is not None:
            mock_file_format_adapter.deserialize.return_value = deserialized_data
        else:
            mock_file_format_adapter.deserialize.side_effect = Exception("Deserialization error")
        mock_get_adapter.return_value = mock_file_format_adapter

        if should_fail:
            with pytest.raises(Exception):
                config_loader.load(loader_name)
            mock_logger.error.assert_called()
        else:
            result = config_loader.load(loader_name)
            assert isinstance(result, AppConfigEntity)
            assert result.common == deserialized_data["common"]
            assert result.connectors_configurations == deserialized_data["connectors_configurations"]
            assert result.metrics == deserialized_data["metrics"]
            assert result.attack_modules == deserialized_data["attack_modules"]
            mock_logger.error.assert_not_called()