import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from azure.core.exceptions import ResourceNotFoundError, AzureError
from azure.storage.blob import BlobClient, ContainerClient

from adapters.storage_provider.azure_blob_storage_adapter import AzureBlobStorageAdapter
from domain.services.enums.module_types import ModuleTypes


@pytest.fixture
def azure_blob_storage_adapter():
    """
    Fixture to create a mocked AzureBlobStorageAdapter instance.
    """
    with patch('adapters.storage_provider.azure_blob_storage_adapter.BlobServiceClient') as mock_client:
        adapter = AzureBlobStorageAdapter()
        adapter.blob_service_client = mock_client.from_connection_string.return_value
        return adapter


@pytest.fixture
def mock_azure_blob_storage_client():
    """
    Fixture to create a mock Azure Blob Storage client.
    
    Returns:
        MagicMock: A mock Azure Blob Storage client.
    """
    return MagicMock(spec=BlobClient)


@pytest.fixture
def mock_azure_blob_storage_container():
    return MagicMock(spec=ContainerClient)


class TestAzureBlobStorageAdapter:
    """
    Test suite for AzureBlobStorageAdapter class.
    """

    def test_init(self):
        with patch('adapters.storage_provider.azure_blob_storage_adapter.BlobServiceClient') as mock_client:
            adapter = AzureBlobStorageAdapter()
            mock_client.assert_called_once()
            assert adapter.blob_service_client == mock_client.return_value

    @pytest.mark.parametrize("path, expected", [
        ("https://testblobstorage.blob.core.windows.net/containername/test.yaml", True),
        ("https://testblobstorage.blob.core.windows.net/containername/test.json", True),
        ("/local/path/file.txt", False),
        ("http://example.com/file.txt", False),
        ("", False),
    ])
    def test_supports(self, path, expected):
        """
        Test the supports method with various path formats.
        
        Args:
            path (str): The path to test.
            expected (bool): The expected result.
        """
        assert AzureBlobStorageAdapter.supports(path) == expected

    @pytest.mark.parametrize("file_path, expected_container, expected_blob", [
        ("https://x.blob.core.windows.net/mycontainer/myfile.py", "mycontainer", "myfile.py"),
        ("https://x.blob.core.windows.net/test-container/test.yaml", "test-container", "test.yaml"),
    ])
    def test_extract_container_and_blob_success(self, file_path, expected_container, expected_blob):
        """
        Test successful extraction of Azure Blob Storage container and blob from valid paths.
        
        Args:
            file_path (str): The Azure Blob Storage path to parse.
            expected_container (str): The expected container name.
            expected_blob (str): The expected blob name.
        """
        container, blob = AzureBlobStorageAdapter.extract_container_and_blob(file_path)
        assert container == expected_container
        assert blob == expected_blob

    @pytest.mark.parametrize("invalid_path", [
        "container/file.txt",
        "https://x.blob.core.windows.bucket/file.txt",
        "https://x.blob.core.windows.net/test.yaml",
        "",
    ])
    def test_extract_container_and_blob_invalid_path(self, invalid_path):
        """
        Test extraction failure with invalid Azure Blob Storage paths
        Args:
            invalid_path (str): Invalid path that should raise ValueError.
        """
        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            with pytest.raises(ValueError):
                AzureBlobStorageAdapter.extract_container_and_blob(invalid_path)
            mock_logger.error.assert_called_once()
    
    def test_read_file_success(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test successful file reading from Azure Blob Storage.
        """
        mock_azure_blob_storage_client.download_blob.return_value.readall.return_value = b"file content"
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)

        content = azure_blob_storage_adapter.read_file("https://account.blob.core.windows.net/container/file.txt")
        assert content == "file content"
        azure_blob_storage_adapter.blob_service_client.get_blob_client.assert_called_once()

    def test_read_file_not_found(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test reading a non-existent file from Azure Blob Storage.
        """
        mock_azure_blob_storage_client.download_blob.side_effect = ResourceNotFoundError("Blob not found")
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)

        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            content = azure_blob_storage_adapter.read_file("https://account.blob.core.windows.net/container/missing.txt")
            assert content is None
            mock_logger.warning.assert_called_once()

    def test_read_file_general_exception(self, azure_blob_storage_adapter):
        """
        Test reading file with a general exception (simulating connection error).
        """
        azure_blob_storage_adapter.blob_service_client.exceptions = MagicMock()
        azure_blob_storage_adapter.blob_service_client.exceptions.ResourceNotFoundError = ResourceNotFoundError
        mock_blob_client = MagicMock()

        mock_stream = MagicMock()
        mock_stream.readall.side_effect = Exception("Connection error")
        mock_blob_client.download_blob.return_value = mock_stream
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_blob_client)

        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            content = azure_blob_storage_adapter.read_file(
                "https://x.blob.core.windows.net/mycontainer/myfile.py"
            )
            assert content is None

            mock_logger.error.assert_called_once()
            logged_message = mock_logger.error.call_args[0][0]
            assert "Connection error" in logged_message

    def test_write_file_success_string_content(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test successful file writing to Azure Blob Storage with string content.
        """
        azure_blob_storage_adapter.exists = MagicMock(return_value=False)
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)

        result = azure_blob_storage_adapter.write_file(
            "https://account.blob.core.windows.net/container/file.txt", "hello world"
        )

        assert result is True
        args, kwargs = mock_azure_blob_storage_client.upload_blob.call_args
        assert args[0] == b"hello world"
        assert kwargs.get("overwrite") is False

    def test_write_file_success_dict_content(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test successful file writing to Azure Blob Storage with dictionary content.
        """
        azure_blob_storage_adapter.exists = MagicMock(return_value=False)
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)
        test_dict = {"key": "value", "number": 42}

        result = azure_blob_storage_adapter.write_file(
            "https://account.blob.core.windows.net/container/file.json", test_dict
        )
        assert result is True
        expected_bytes = json.dumps(test_dict).encode("utf-8")
        mock_azure_blob_storage_client.upload_blob.assert_called_once_with(expected_bytes, overwrite=False)

    def test_write_file_already_exists(self, azure_blob_storage_adapter):
        """
        Test writing to an existing file in Azure Blob Storage.
        """
        azure_blob_storage_adapter.exists = MagicMock(return_value=True)
        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            result = azure_blob_storage_adapter.write_file(
                "https://account.blob.core.windows.net/container/file.txt", "data"
            )
            assert result is False
            mock_logger.error.assert_called_once()

    def test_write_file_general_exception(self, azure_blob_storage_adapter):
        """
        Test file writing with general exception.
        """
        azure_blob_storage_adapter.exists = MagicMock(return_value=False)
        mock_blob_client = MagicMock()
        mock_blob_client.upload_blob.side_effect = Exception("Upload error")
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_blob_client)

        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            result = azure_blob_storage_adapter.write_file(
                "https://x.blob.core.windows.net/mycontainer/myfile.p", "content"
            )
            assert result is False

            mock_logger.error.assert_called_once()
            logged_message = mock_logger.error.call_args[0][0]
            assert "Upload error" in logged_message
    
    def test_list_blobs_success_with_contents(self, azure_blob_storage_adapter, mock_azure_blob_storage_container):
        """
        Test successful listing of files in Azure Blob Storage container with contents.
        """
        mock_azure_blob_storage_container.list_blobs.return_value = [
            MagicMock(name="file1.txt"),
            MagicMock(name="file2.txt")
        ]
        azure_blob_storage_adapter.blob_service_client.get_container_client = MagicMock(return_value=mock_azure_blob_storage_container)

        files = azure_blob_storage_adapter.list("https://account.blob.core.windows.net/container/")
        assert len(files) == 2

    def test_list_blobs_success_empty_directory(self, azure_blob_storage_adapter):
        """
        Test successful listing of empty Azure Blob Storage container.
        """
        mock_response = {}
        azure_blob_storage_adapter.blob_service_client.get_container_client = MagicMock(return_value=mock_response)

        files = azure_blob_storage_adapter.list("https://account.blob.core.windows.net/container/")
        assert len(files) == 0
    
    def test_exists_blob_exists(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test checking existence of an existing file in Azure Blob Storage.
        """
        # Mock blob_client.exists() to return True
        mock_azure_blob_storage_client.exists.return_value = True
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)

        result = azure_blob_storage_adapter.exists("https://account.blob.core.windows.net/container/file.txt")
        assert result is True

    def test_exists_blob_not_found(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test checking existence of a non-existent file in Azure Blob Storage.
        """
        # Mock blob_client.exists() to return False
        mock_azure_blob_storage_client.exists.return_value = False
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)

        result = azure_blob_storage_adapter.exists("https://account.blob.core.windows.net/container/missing.txt")
        assert result is False

    def test_exists_client_error_non_404(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test file existence check with non-404 client error.
        """
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)
        mock_azure_blob_storage_client.exists.side_effect = AzureError("Forbidden")
        
        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            import pytest
            with pytest.raises(AzureError):
                azure_blob_storage_adapter.exists("https://account.blob.core.windows.net/container/file.txt")
            
            mock_logger.error.assert_called_once()
            logged_message = mock_logger.error.call_args[0][0]
            assert "Forbidden" in logged_message
    
    def test_exists_general_exception(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test file existence check with general exception.
        """
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)
        mock_azure_blob_storage_client.exists.side_effect = AzureError("Connection error")

        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            with pytest.raises(AzureError, match="Connection error"):
                azure_blob_storage_adapter.exists(
                    "https://account.blob.core.windows.net/container/file.txt"
                )

            mock_logger.error.assert_called_once()
            assert "Connection error" in mock_logger.error.call_args[0][0]
    
    def test_get_creation_datetime_success(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test successful retrieval of file creation datetime from Azure Blob Storage.
        """
        mock_datetime = datetime(2023, 1, 1, 12, 0, 0)
        mock_azure_blob_storage_client.get_blob_properties.return_value = MagicMock(last_modified=mock_datetime)
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)

        timestamp = azure_blob_storage_adapter.get_creation_datetime("https://account.blob.core.windows.net/container/file.txt")
        assert timestamp == mock_datetime.timestamp()

    def test_get_creation_datetime_not_found(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test getting creation datetime for non-existent file in Azure Blob Storage.
        """
        mock_azure_blob_storage_client.get_blob_properties.side_effect = ResourceNotFoundError()
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)

        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            timestamp = azure_blob_storage_adapter.get_creation_datetime("https://account.blob.core.windows.net/container/missing.txt")
            assert timestamp is None
            mock_logger.warning.assert_called_once()

    def test_get_creation_datetime_client_error_non_404(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test getting creation datetime with non-404 client error.
        Test focus on forbidden error 403 code
        """
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)
        mock_azure_blob_storage_client.get_blob_properties.side_effect = AzureError("Forbidden")

        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            with pytest.raises(AzureError, match="Forbidden"):
                azure_blob_storage_adapter.get_creation_datetime(
                    "https://account.blob.core.windows.net/container/file.txt"
                )

            mock_logger.error.assert_called_once()
            assert "Forbidden" in mock_logger.error.call_args[0][0]
    
    def test_download_file_from_azure_blob_storage_success(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test successful file download from Azure Blob Storage.
        """
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)
        
        # Mock download_blob().readall()
        mock_azure_blob_storage_client.download_blob.return_value.readall.return_value = b"data"

        # Mock open() so no actual file is created
        with patch("builtins.open", mock_open()) as mocked_file:
            result = azure_blob_storage_adapter.download_file(
                "container", "file.txt", "/local/file.txt"
            )
            assert result == "/local/file.txt"
            mocked_file.assert_called_once_with("/local/file.txt", "wb")
            mocked_file().write.assert_called_once_with(b"data")

    def test_download_file_from_azure_blob_storage_exception(self, azure_blob_storage_adapter, mock_azure_blob_storage_client):
        """
        Test file download from Azure Blob Storage with exception.
        """
        azure_blob_storage_adapter.blob_service_client.get_blob_client = MagicMock(return_value=mock_azure_blob_storage_client)
        
        # Mock download_blob() to raise an exception
        mock_azure_blob_storage_client.download_blob.side_effect = AzureError("Download failed")

        with patch("builtins.open", mock_open()):
            with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
                with pytest.raises(AzureError):
                    azure_blob_storage_adapter.download_file(
                        "container", "file.txt", "/local/file.txt"
                    )
                mock_logger.error.assert_called_once()

    @patch('adapters.storage_provider.azure_blob_storage_adapter.get_instance')
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_load_module_success(self, mock_join, mock_makedirs, mock_get_instance, azure_blob_storage_adapter):
        # Mock path joining
        mock_join.side_effect = lambda *args: "/".join(args)
        # Mock get_instance to return a valid module instance
        mock_get_instance.return_value = MagicMock()
        # Patch download_file to prevent actual filesystem write
        with patch.object(azure_blob_storage_adapter, 'download_file', return_value='/temp/attack_module/test_module.py'):
            with patch('adapters.storage_provider.azure_blob_storage_adapter.AppConfig') as mock_app_config:
                mock_app_config.DEFAULT_TEMP_PATH = "/temp"  # <-- patch here

                instance, file_id = azure_blob_storage_adapter.load_module(
                    "https://account.blob.core.windows.net/container/modules/test_module",
                    ModuleTypes.ATTACK_MODULE,
                    "https://account.blob.core.windows.net/container/modules/test_module"
                )

                assert instance == mock_get_instance.return_value
                assert file_id == "test_module"
                mock_makedirs.assert_called_once_with("/temp/attack_module", exist_ok=True)

    @patch('adapters.storage_provider.azure_blob_storage_adapter.get_instance')
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_load_module_get_instance_none(self, mock_join, mock_makedirs, mock_get_instance, azure_blob_storage_adapter):
        mock_join.side_effect = lambda *args: "/".join(args)
        mock_get_instance.return_value = None
        # Patch download_file to avoid real filesystem writes
        with patch.object(azure_blob_storage_adapter, 'download_file', return_value='/temp/attack_module/test_module.py'):
            with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
                import pytest
                with pytest.raises(Exception, match="Failed to load module from path"):
                    azure_blob_storage_adapter.load_module(
                        "https://account.blob.core.windows.net/container/modules/test_module",
                        ModuleTypes.ATTACK_MODULE,
                        "https://account.blob.core.windows.net/container/modules/test_module"
                    )
                # Ensure logger.error was called at least once
                mock_logger.error.assert_called()

    def test_load_module_exception(self, azure_blob_storage_adapter):
        # Patch extract_container_and_blob to raise an exception
        azure_blob_storage_adapter.extract_container_and_blob = MagicMock(side_effect=Exception("Extract error"))
        with patch('adapters.storage_provider.azure_blob_storage_adapter.logger') as mock_logger:
            import pytest
            with pytest.raises(Exception):
                azure_blob_storage_adapter.load_module(
                    "https://account.blob.core.windows.net/container/modules/test_module",
                    ModuleTypes.ATTACK_MODULE,
                    "https://account.blob.core.windows.net/container/modules/test_module"
                )
            # Check that logger.error was called at least once
            mock_logger.error.assert_called()
            # Optionally, check that the error message contains "Extract error"
            assert any("Extract error" in str(call.args) for call in mock_logger.error.call_args_list)
        