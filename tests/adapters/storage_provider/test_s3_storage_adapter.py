import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from botocore.exceptions import ClientError

from adapters.storage_provider.s3_storage_adapter import S3StorageAdapter
from domain.services.enums.module_types import ModuleTypes


@pytest.fixture
def s3_storage_adapter():
    """
    Fixture to create a mocked S3StorageAdapter instance.
    
    Returns:
        S3StorageAdapter: An instance with mocked boto3 client.
    """
    with patch('boto3.client'):
        return S3StorageAdapter()


@pytest.fixture
def mock_s3_client():
    """
    Fixture to create a mock S3 client.
    
    Returns:
        MagicMock: A mock S3 client.
    """
    return MagicMock()


class TestS3StorageAdapter:
    """
    Test suite for S3StorageAdapter class.
    """
    
    def test_init(self):
        """
        Test S3StorageAdapter initialization.
        """
        with patch('boto3.client') as mock_boto3_client:
            adapter = S3StorageAdapter()
            mock_boto3_client.assert_called_once_with("s3")
            assert adapter.s3_client == mock_boto3_client.return_value

    @pytest.mark.parametrize("path, expected", [
        ("s3://bucket/file.txt", True),
        ("s3://my-bucket/path/to/file.json", True),
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
        assert S3StorageAdapter.supports(path) == expected

    @pytest.mark.parametrize("file_path, expected_bucket, expected_key", [
        ("s3://bucket/file.txt", "bucket", "file.txt"),
        ("s3://my-bucket/path/to/file.json", "my-bucket", "path/to/file.json"),
        ("s3://test-bucket/folder/subfolder/data.csv", "test-bucket", "folder/subfolder/data.csv"),
    ])
    def test_extract_s3_bucket_and_key_success(self, file_path, expected_bucket, expected_key):
        """
        Test successful extraction of S3 bucket and key from valid paths.
        
        Args:
            file_path (str): The S3 path to parse.
            expected_bucket (str): The expected bucket name.
            expected_key (str): The expected key.
        """
        bucket, key = S3StorageAdapter.extract_s3_bucket_and_key(file_path)
        assert bucket == expected_bucket
        assert key == expected_key

    @pytest.mark.parametrize("invalid_path", [
        "bucket/file.txt",
        "http://bucket/file.txt",
        "ftp://bucket/file.txt",
        "",
    ])
    def test_extract_s3_bucket_and_key_invalid_path(self, invalid_path):
        """
        Test extraction failure with invalid S3 paths.
        
        Args:
            invalid_path (str): Invalid path that should raise ValueError.
        """
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            with pytest.raises(ValueError):
                S3StorageAdapter.extract_s3_bucket_and_key(invalid_path)
            mock_logger.error.assert_called_once()

    def test_extract_s3_bucket_and_key_malformed_path(self):
        """
        Test extraction failure with malformed S3 path (bucket only).
        """
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            with pytest.raises(ValueError):
                S3StorageAdapter.extract_s3_bucket_and_key("s3://bucket-only")
            mock_logger.error.assert_called_once()

    def test_read_file_success(self, s3_storage_adapter):
        """
        Test successful file reading from S3.
        """
        # Mock S3 response - need to properly mock the context manager behavior
        mock_body = MagicMock()
        mock_body.__enter__.return_value = mock_body
        mock_body.__exit__.return_value = None
        mock_body.read.return_value = b"file content"
        mock_response = {"Body": mock_body}
        s3_storage_adapter.s3_client.get_object.return_value = mock_response

        content = s3_storage_adapter.read_file("s3://bucket/file.txt")
        
        assert content == "file content"
        s3_storage_adapter.s3_client.get_object.assert_called_once_with(
            Bucket="bucket", Key="file.txt"
        )

    def test_read_file_not_found(self, s3_storage_adapter):
        """
        Test reading a non-existent file from S3.
        """
        # Mock NoSuchKey exception
        s3_storage_adapter.s3_client.exceptions.NoSuchKey = Exception
        s3_storage_adapter.s3_client.get_object.side_effect = s3_storage_adapter.s3_client.exceptions.NoSuchKey

        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            content = s3_storage_adapter.read_file("s3://bucket/nonexistent.txt")
            
            assert content is None
            mock_logger.warning.assert_called_once_with(
                S3StorageAdapter.WARNING_FILE_NOT_FOUND.format(file_path="s3://bucket/nonexistent.txt")
            )

    def test_read_file_general_exception(self, s3_storage_adapter):
        """
        Test reading file with general exception.
        """
        # Mock exceptions attribute to avoid TypeError
        s3_storage_adapter.s3_client.exceptions = MagicMock()
        s3_storage_adapter.s3_client.exceptions.NoSuchKey = type('NoSuchKey', (Exception,), {})
        s3_storage_adapter.s3_client.get_object.side_effect = Exception("Connection error")

        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            content = s3_storage_adapter.read_file("s3://bucket/file.txt")
            
            assert content is None
            mock_logger.error.assert_called_once_with(
                S3StorageAdapter.ERROR_READ_FILE.format(error="Connection error")
            )

    def test_write_file_success_string_content(self, s3_storage_adapter):
        """
        Test successful file writing to S3 with string content.
        """
        s3_storage_adapter.exists = MagicMock(return_value=False)
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            result = s3_storage_adapter.write_file("s3://bucket/file.txt", "test content")
            
            assert result is True
            s3_storage_adapter.s3_client.put_object.assert_called_once_with(
                Bucket="bucket", Key="file.txt", Body=b"test content"
            )
            mock_logger.info.assert_called_once_with(
                S3StorageAdapter.SUCCESS_WRITE_FILE.format(file_path="s3://bucket/file.txt")
            )

    def test_write_file_success_dict_content(self, s3_storage_adapter):
        """
        Test successful file writing to S3 with dictionary content.
        """
        s3_storage_adapter.exists = MagicMock(return_value=False)
        test_dict = {"key": "value", "number": 42}
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            result = s3_storage_adapter.write_file("s3://bucket/file.json", test_dict)
            
            assert result is True
            expected_content = json.dumps(test_dict).encode('utf-8')
            s3_storage_adapter.s3_client.put_object.assert_called_once_with(
                Bucket="bucket", Key="file.json", Body=expected_content
            )

    def test_write_file_already_exists(self, s3_storage_adapter):
        """
        Test writing to an existing file in S3.
        """
        s3_storage_adapter.exists = MagicMock(return_value=True)
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            result = s3_storage_adapter.write_file("s3://bucket/file.txt", "content")
            
            assert result is False
            mock_logger.error.assert_called_once_with(
                S3StorageAdapter.FILE_EXIST_ERROR.format(file_path="s3://bucket/file.txt")
            )
            s3_storage_adapter.s3_client.put_object.assert_not_called()

    def test_write_file_general_exception(self, s3_storage_adapter):
        """
        Test file writing with general exception.
        """
        s3_storage_adapter.exists = MagicMock(return_value=False)
        s3_storage_adapter.s3_client.put_object.side_effect = Exception("Upload error")
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            result = s3_storage_adapter.write_file("s3://bucket/file.txt", "content")
            
            assert result is False
            mock_logger.error.assert_called_once_with(
                S3StorageAdapter.ERROR_WRITE_FILE.format(error="Upload error")
            )

    def test_list_success_with_contents(self, s3_storage_adapter):
        """
        Test successful listing of files in S3 directory with contents.
        """
        mock_response = {
            "Contents": [
                {"Key": "folder/file1.txt"},
                {"Key": "folder/file2.txt"},
                {"Key": "folder/subfolder/file3.txt"}
            ]
        }
        s3_storage_adapter.s3_client.list_objects_v2.return_value = mock_response
        
        files = s3_storage_adapter.list("s3://bucket/folder/")
        
        assert files == ["folder/file1.txt", "folder/file2.txt", "folder/subfolder/file3.txt"]
        s3_storage_adapter.s3_client.list_objects_v2.assert_called_once_with(
            Bucket="bucket", Prefix="folder/"
        )

    def test_list_success_empty_directory(self, s3_storage_adapter):
        """
        Test listing of empty S3 directory.
        """
        mock_response = {}  # No "Contents" key
        s3_storage_adapter.s3_client.list_objects_v2.return_value = mock_response
        
        files = s3_storage_adapter.list("s3://bucket/empty/")
        
        assert files == []

    def test_exists_file_exists(self, s3_storage_adapter):
        """
        Test checking existence of an existing file in S3.
        """
        s3_storage_adapter.s3_client.head_object.return_value = {}
        
        result = s3_storage_adapter.exists("s3://bucket/file.txt")
        
        assert result is True
        s3_storage_adapter.s3_client.head_object.assert_called_once_with(
            Bucket="bucket", Key="file.txt"
        )

    def test_exists_file_not_found(self, s3_storage_adapter):
        """
        Test checking existence of a non-existent file in S3.
        """
        error_response = {"Error": {"Code": "404"}}
        s3_storage_adapter.s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")
        
        result = s3_storage_adapter.exists("s3://bucket/nonexistent.txt")
        
        assert result is False

    def test_exists_client_error_non_404(self, s3_storage_adapter):
        """
        Test file existence check with non-404 client error.
        """
        error_response = {"Error": {"Code": "403"}}
        s3_storage_adapter.s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            with pytest.raises(ClientError):
                s3_storage_adapter.exists("s3://bucket/file.txt")
            mock_logger.error.assert_called_once()

    def test_exists_general_exception(self, s3_storage_adapter):
        """
        Test file existence check with general exception.
        """
        s3_storage_adapter.s3_client.head_object.side_effect = Exception("Connection error")
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            with pytest.raises(Exception):
                s3_storage_adapter.exists("s3://bucket/file.txt")
            mock_logger.error.assert_called_once()

    def test_get_creation_datetime_success(self, s3_storage_adapter):
        """
        Test successful retrieval of file creation datetime from S3.
        """
        mock_datetime = datetime(2023, 1, 1, 12, 0, 0)
        mock_response = {"LastModified": mock_datetime}
        s3_storage_adapter.s3_client.head_object.return_value = mock_response
        
        result = s3_storage_adapter.get_creation_datetime("s3://bucket/file.txt")
        
        assert result == mock_datetime.timestamp()
        s3_storage_adapter.s3_client.head_object.assert_called_once_with(
            Bucket="bucket", Key="file.txt"
        )

    def test_get_creation_datetime_file_not_found(self, s3_storage_adapter):
        """
        Test getting creation datetime for non-existent file in S3.
        """
        error_response = {"Error": {"Code": "404"}}
        s3_storage_adapter.s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            result = s3_storage_adapter.get_creation_datetime("s3://bucket/nonexistent.txt")
            
            assert result is None
            mock_logger.warning.assert_called_once_with(
                S3StorageAdapter.WARNING_FILE_NOT_FOUND.format(file_path="s3://bucket/nonexistent.txt")
            )

    def test_get_creation_datetime_client_error_non_404(self, s3_storage_adapter):
        """
        Test getting creation datetime with non-404 client error.
        """
        error_response = {"Error": {"Code": "403"}}
        s3_storage_adapter.s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            with pytest.raises(ClientError):
                s3_storage_adapter.get_creation_datetime("s3://bucket/file.txt")
            mock_logger.error.assert_called_once()

    def test_download_file_from_s3_success(self, s3_storage_adapter):
        """
        Test successful file download from S3.
        """
        result = s3_storage_adapter.download_file_from_s3("bucket", "file.py", "/local/path/file.py")
        
        assert result == "/local/path/file.py"
        s3_storage_adapter.s3_client.download_file.assert_called_once_with(
            "bucket", "file.py", "/local/path/file.py"
        )

    def test_download_file_from_s3_exception(self, s3_storage_adapter):
        """
        Test file download from S3 with exception.
        """
        s3_storage_adapter.s3_client.download_file.side_effect = Exception("Download error")
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            with pytest.raises(Exception):
                s3_storage_adapter.download_file_from_s3("bucket", "file.py", "/local/path/file.py")
            mock_logger.error.assert_called_once_with(
                S3StorageAdapter.ERROR_DOWNlOAD_FILE.format(error="Download error")
            )

    @patch('adapters.storage_provider.s3_storage_adapter.get_instance')
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_load_module_success(self, mock_join, mock_makedirs, mock_get_instance, s3_storage_adapter):
        """
        Test successful module loading from S3.
        """
        # Setup mocks
        mock_join.side_effect = lambda *args: "/".join(args)
        mock_get_instance.return_value = MagicMock()
        s3_storage_adapter.download_file_from_s3 = MagicMock(return_value="/local/temp/module.py")
        
        with patch('adapters.storage_provider.s3_storage_adapter.AppConfig') as mock_app_config:
            mock_app_config.DEFAULT_TEMP_PATH = "/temp"
            
            instance, file_id = s3_storage_adapter.load_module(
                "s3://bucket/modules/test_module", 
                ModuleTypes.ATTACK_MODULE, 
                "s3://bucket/modules/test_module"
            )
            
            assert instance == mock_get_instance.return_value
            assert file_id == "test_module"
            mock_makedirs.assert_called_once_with("/temp/attack_module", exist_ok=True)
            s3_storage_adapter.download_file_from_s3.assert_called_once_with(
                "bucket", "modules/test_module.py", "/temp/attack_module/test_module.py"
            )

    @patch('adapters.storage_provider.s3_storage_adapter.get_instance')
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_load_module_get_instance_returns_none(self, mock_join, mock_makedirs, mock_get_instance, s3_storage_adapter):
        """
        Test module loading when get_instance returns None.
        """
        # Setup mocks
        mock_join.side_effect = lambda *args: "/".join(args)
        mock_get_instance.return_value = None
        s3_storage_adapter.download_file_from_s3 = MagicMock(return_value="/local/temp/module.py")
        
        with patch('adapters.storage_provider.s3_storage_adapter.AppConfig') as mock_app_config:
            mock_app_config.DEFAULT_TEMP_PATH = "/temp"
            
            with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
                with pytest.raises(Exception, match="Failed to load module from path"):
                    s3_storage_adapter.load_module(
                        "s3://bucket/modules/test_module", 
                        ModuleTypes.ATTACK_MODULE, 
                        "s3://bucket/modules/test_module"
                    )
                mock_logger.error.assert_called_once()

    def test_load_module_exception(self, s3_storage_adapter):
        """
        Test module loading with exception during extraction.
        """
        s3_storage_adapter.extract_s3_bucket_and_key = MagicMock(side_effect=Exception("Extract error"))
        
        with patch('adapters.storage_provider.s3_storage_adapter.logger') as mock_logger:
            with pytest.raises(Exception):
                s3_storage_adapter.load_module(
                    "s3://bucket/modules/test_module", 
                    ModuleTypes.ATTACK_MODULE, 
                    "s3://bucket/modules/test_module"
                )
            mock_logger.error.assert_called_once_with(
                S3StorageAdapter.ERROR_LOAD_MODULE.format(error="Extract error")
            )
