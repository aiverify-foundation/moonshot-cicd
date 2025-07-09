import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from domain.services.loader.loader_types.dataset_loader import DatasetLoader
from domain.services.app_config import AppConfig
from domain.entities.dataset_entity import DatasetEntity
from domain.ports.storage_provider_port import StorageProviderPort

@pytest.fixture
def mock_storage_adapter():
    return Mock(spec=StorageProviderPort)

@pytest.fixture
def dataset_loader(mock_storage_adapter):
    return DatasetLoader(mock_storage_adapter)

@pytest.mark.parametrize("file_exists, file_content, should_raise_exception", [
    (True, '{"name": "test_dataset", "description": "A test dataset", "examples": []}', False),  # Valid file scenario
    (False, None, True),                                        # File not found scenario
    (True, None, True),                                         # File read error scenario
])
def test_load(dataset_loader, mock_storage_adapter, file_exists, file_content, should_raise_exception):
    mock_storage_adapter.exists.return_value = file_exists
    mock_storage_adapter.read_file.return_value = file_content

    with patch.object(DatasetLoader, '_get_creation_datetime', return_value=datetime(2023, 1, 1, 12, 0, 0)), \
         patch('domain.services.loader.factory.file_format_factory.FileFormatFactory.get_adapter') as mock_get_adapter:
        
        # Mock the file format adapter
        mock_adapter = Mock()
        mock_get_adapter.return_value = mock_adapter
        mock_adapter.deserialize.return_value = {"name": "test_dataset", "description": "A test dataset", "examples": []}
        
        if should_raise_exception:
            with pytest.raises(Exception):
                dataset_loader.load("test_dataset")
        else:
            dataset = dataset_loader.load("test_dataset")
            assert isinstance(dataset, DatasetEntity), "Expected a DatasetEntity instance"

@pytest.mark.parametrize("timestamp, should_raise_exception", [
    (datetime.now().timestamp(), False),  # Valid timestamp scenario
    (None, True),                         # Error getting timestamp scenario
])
def test_get_creation_datetime(dataset_loader, mock_storage_adapter, timestamp, should_raise_exception):
    mock_storage_adapter.get_creation_datetime.return_value = timestamp

    if should_raise_exception:
        with pytest.raises(Exception):
            dataset_loader._get_creation_datetime("test_dataset")
    else:
        creation_datetime = dataset_loader._get_creation_datetime("test_dataset")
        assert isinstance(creation_datetime, datetime), "Expected a datetime instance"

@pytest.mark.parametrize("file_content, should_raise_exception", [
    ('{"name": "test_dataset", "examples": []}', False),  # Valid JSON scenario
    ('invalid_json', True),                               # Invalid JSON scenario
])
def test_deserialize_content(dataset_loader, file_content, should_raise_exception):
    with patch('domain.services.loader.factory.file_format_factory.FileFormatFactory.get_adapter') as mock_get_adapter:
        mock_adapter = Mock()
        mock_get_adapter.return_value = mock_adapter
        mock_adapter.deserialize.side_effect = Exception("Deserialization error") if should_raise_exception else lambda x: {"name": "test_dataset", "examples": []}

        if should_raise_exception:
            with pytest.raises(Exception):
                dataset_loader._deserialize_content("test_dataset", file_content)
        else:
            content = dataset_loader._deserialize_content("test_dataset", file_content)
            assert isinstance(content, dict), "Expected a dictionary"
