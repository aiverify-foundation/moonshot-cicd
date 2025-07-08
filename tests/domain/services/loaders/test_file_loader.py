import pytest
from unittest.mock import patch, MagicMock
from domain.services.enums.file_types import FileTypes
from domain.services.loader.file_loader import FileLoader
from domain.services.loader.loader_types.config_loader import ConfigLoader
from domain.services.loader.loader_types.dataset_loader import DatasetLoader
from domain.services.loader.loader_types.test_config_loader import TestConfigLoader

@pytest.mark.parametrize("file_name, file_type, expected_loader, expected_exception", [
    ('config.yaml', FileTypes.CONFIG, ConfigLoader, None),
    ('dataset.csv', FileTypes.DATASET, DatasetLoader, None),
    ('test_config.yaml', FileTypes.TEST_CONFIG, TestConfigLoader, None),
    ('unknown_file', "UKNOWN", None, Exception)
])
@patch('domain.services.loader.file_loader.StorageProviderFactory.get_adapter')
def test_file_loader_load(mock_get_adapter, file_name, file_type, expected_loader, expected_exception):
    # Mock the storage adapter
    mock_storage_adapter = MagicMock()
    mock_get_adapter.return_value = mock_storage_adapter

    if expected_exception:
        with pytest.raises(expected_exception):
            FileLoader.load(file_name, file_type)
    else:
        # Mock the loader
        mock_loader_instance = MagicMock()
        with patch.object(expected_loader, 'load', return_value=mock_loader_instance) as mock_load:
            # Test loading the file
            result = FileLoader.load(file_name, file_type)
            mock_load.assert_called_once_with(file_name)
            assert result == mock_loader_instance