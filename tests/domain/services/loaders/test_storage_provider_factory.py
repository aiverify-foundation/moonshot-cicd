import pytest
from unittest.mock import patch
from domain.services.loader.factory.storage_provider_factory import StorageProviderFactory
from adapters.storage_provider.s3_storage_adapter import S3StorageAdapter
from adapters.storage_provider.local_storage_adapter import LocalStorageAdapter

@pytest.fixture(autouse=True)
def setup_adapters():
    # Clear any previously registered adapters
    StorageProviderFactory._adapters = []
    StorageProviderFactory._fallback_adapter = None

    # Register real adapters
    StorageProviderFactory.register_adapter(S3StorageAdapter)
    StorageProviderFactory.register_adapter(LocalStorageAdapter)
    StorageProviderFactory._fallback_adapter = LocalStorageAdapter

@pytest.mark.parametrize("path, expected_adapter_cls", [
    ("s3://bucket/file", S3StorageAdapter),
    ("/local/path/file.txt", LocalStorageAdapter),
])
def test_get_adapter(path, expected_adapter_cls):
    with patch('domain.services.loader.factory.storage_provider_factory.logger') as mock_logger:
        adapter = StorageProviderFactory.get_adapter(path)
        assert isinstance(adapter, expected_adapter_cls)
        if expected_adapter_cls is LocalStorageAdapter:
            mock_logger.warning.assert_called_once_with(
                StorageProviderFactory.WARNING_NO_ADAPTER_FOUND.format(path=path)
            )
        else:
            mock_logger.warning.assert_not_called()