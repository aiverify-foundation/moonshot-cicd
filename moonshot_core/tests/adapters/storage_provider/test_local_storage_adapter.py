import pytest
from unittest.mock import patch, mock_open, MagicMock
from adapters.storage_provider.local_storage_adapter import LocalStorageAdapter

@pytest.fixture
def local_storage_adapter():
    """
    Fixture to create a LocalStorageAdapter instance for testing.
    
    Returns:
        LocalStorageAdapter: An instance of LocalStorageAdapter.
    """
    return LocalStorageAdapter()

def test_supports(local_storage_adapter):
    """
    Test that LocalStorageAdapter supports any file path.
    """
    assert local_storage_adapter.supports("any_path") is True

# Tests for load_module method
@patch("adapters.storage_provider.local_storage_adapter.get_instance")
def test_load_module_success(mock_get_instance, local_storage_adapter):
    """
    Test successful module loading from local storage.
    """
    # Setup
    mock_instance = MagicMock()
    mock_get_instance.return_value = mock_instance
    file_path = "test_module.py"
    module_type = "test_type"
    complete_path = "/full/path/to/test_module.py"
    
    # Execute
    result_instance, result_file_path = local_storage_adapter.load_module(file_path, module_type, complete_path)
    
    # Assert
    assert result_instance == mock_instance
    assert result_file_path == file_path
    mock_get_instance.assert_called_once_with(file_path, complete_path)

@patch("adapters.storage_provider.local_storage_adapter.get_instance")
def test_load_module_returns_none(mock_get_instance, local_storage_adapter):
    """
    Test module loading when get_instance returns None.
    """
    # Setup
    mock_get_instance.return_value = None
    file_path = "test_module.py"
    module_type = "test_type"
    complete_path = "/full/path/to/test_module.py"
    
    with patch("adapters.storage_provider.local_storage_adapter.logger") as mock_logger:
        # Execute & Assert
        with pytest.raises(Exception, match=f"Failed to load module from path {complete_path}"):
            local_storage_adapter.load_module(file_path, module_type, complete_path)
        
        mock_logger.error.assert_called_once()

@patch("adapters.storage_provider.local_storage_adapter.get_instance")
def test_load_module_get_instance_exception(mock_get_instance, local_storage_adapter):
    """
    Test module loading when get_instance raises an exception.
    """
    # Setup
    original_error = ImportError("Module not found")
    mock_get_instance.side_effect = original_error
    file_path = "test_module.py"
    module_type = "test_type"
    complete_path = "/full/path/to/test_module.py"
    
    with patch("adapters.storage_provider.local_storage_adapter.logger") as mock_logger:
        # Execute & Assert
        with pytest.raises(ImportError):
            local_storage_adapter.load_module(file_path, module_type, complete_path)
        
        expected_log_message = LocalStorageAdapter.ERROR_LOADING_MODULE.format(error=original_error)
        mock_logger.error.assert_called_once_with(expected_log_message)

@patch("builtins.open", new_callable=mock_open, read_data="file content")
@pytest.mark.parametrize("file_path, side_effect, expected_content, log_method, log_message", [
    ("test.txt", None, "file content", None, None),  # Successful read
    ("non_existent.txt", FileNotFoundError, None, "warning", LocalStorageAdapter.WARNING_FILE_NOT_FOUND.format(file_path="non_existent.txt")),  # File not found
    ("error_file.txt", Exception("General error"), None, "error", LocalStorageAdapter.ERROR_READ_FILE.format(error="General error")),  # General exception
])
def test_read_file(mock_file, local_storage_adapter, file_path, side_effect, expected_content, log_method, log_message):
    """
    Test file reading with various scenarios including success, file not found, and general exceptions.
    """
    with patch("os.path.exists", return_value=True):
        with patch("adapters.storage_provider.local_storage_adapter.logger") as mock_logger:
            # Set the side effect for open
            mock_file.side_effect = side_effect

            # Call the method
            content = local_storage_adapter.read_file(file_path)
            assert content == expected_content

            # Check logging
            if log_method:
                getattr(mock_logger, log_method).assert_called_once_with(log_message)
            else:
                mock_logger.warning.assert_not_called()
                mock_logger.error.assert_not_called()

@patch("builtins.open", new_callable=mock_open)
@pytest.mark.parametrize("file_exists, expected_success, expected_message", [
    (False, True, "File written successfully"),
    (True, False, "File already exists"),
])
def test_write_file(mock_file, local_storage_adapter, file_exists, expected_success, expected_message):
    """
    Test file writing with different scenarios for file existence.
    """
    with patch("os.path.exists", return_value=file_exists):
        with patch("os.makedirs") as mock_makedirs, \
             patch("adapters.storage_provider.local_storage_adapter.logger") as mock_logger:
            success, message = local_storage_adapter.write_file("test.txt", "content")
            assert success == expected_success
            assert message == expected_message

            if file_exists:
                mock_logger.error.assert_called_once()
            else:
                mock_file.assert_called_once_with("test.txt", "w")
                mock_file().write.assert_called_once_with("content")
                mock_makedirs.assert_called_once()

@patch("builtins.open", new_callable=mock_open)
def test_write_file_file_exists_error(mock_file, local_storage_adapter):
    """
    Test file writing when file already exists.
    """
    # Simulate file exists
    with patch("os.path.exists", return_value=True):
        with patch("adapters.storage_provider.local_storage_adapter.logger") as mock_logger:
            success, message = local_storage_adapter.write_file("test.txt", "content")
            assert not success
            assert message == "File already exists"
            mock_logger.error.assert_called_once()

@patch("builtins.open", new_callable=mock_open)
def test_write_file_general_exception(mock_file, local_storage_adapter):
    """
    Test file writing with general I/O exception.
    """
    # Simulate a general exception during file writing
    mock_file.side_effect = IOError("General IO error")
    with patch("os.path.exists", return_value=False):
        with patch("os.makedirs") as mock_makedirs, \
             patch("adapters.storage_provider.local_storage_adapter.logger") as mock_logger:
            success, message = local_storage_adapter.write_file("test.txt", "content")
            assert not success
            assert "General IO error" in message
            mock_logger.error.assert_called_once()

@pytest.mark.parametrize("directory_path, expected_files", [
    ("some_directory", ["file1.txt", "file2.txt"]),
    ("empty_directory", []),
])
def test_list_files(local_storage_adapter, directory_path, expected_files):
    """
    Test directory listing with different scenarios.
    """
    with patch("os.listdir", return_value=expected_files):
        files = local_storage_adapter.list(directory_path)
        assert files == expected_files

def test_list_files_exception(local_storage_adapter):
    """
    Test directory listing with exception handling.
    """
    # Test error handling in list method
    directory_path = "non_existent_directory"
    error_message = "Directory not found"
    
    with patch("os.listdir", side_effect=FileNotFoundError(error_message)), \
         patch("adapters.storage_provider.local_storage_adapter.logger") as mock_logger:
        
        result = local_storage_adapter.list(directory_path)
        
        # The method doesn't return anything on error, so result should be None
        assert result is None
        expected_log_message = LocalStorageAdapter.ERROR_LIST_FILE.format(
            directory_path=directory_path, 
            error=FileNotFoundError(error_message)
        )
        mock_logger.error.assert_called_once()

@pytest.mark.parametrize("file_exists", [True, False])
def test_exists(local_storage_adapter, file_exists):
    """
    Test file existence checking.
    """
    with patch("os.path.exists", return_value=file_exists):
        assert local_storage_adapter.exists("test.txt") == file_exists

@pytest.mark.parametrize("file_path, expected_timestamp", [
    ("test.txt", 1234567890.0),
    ("another_file.txt", 9876543210.0),
])
def test_get_creation_datetime(local_storage_adapter, file_path, expected_timestamp):
    """
    Test getting file creation datetime.
    """
    with patch("os.path.getctime", return_value=expected_timestamp):
        timestamp = local_storage_adapter.get_creation_datetime(file_path)
        assert timestamp == expected_timestamp

def test_get_creation_datetime_exception(local_storage_adapter):
    """
    Test getting creation datetime with file not found exception.
    """
    # Test error handling in get_creation_datetime method
    file_path = "non_existent_file.txt"
    
    with patch("os.path.getctime", side_effect=FileNotFoundError("File not found")):
        with pytest.raises(FileNotFoundError):
            local_storage_adapter.get_creation_datetime(file_path)

# Test class constants are properly defined
def test_class_constants():
    """
    Test that all required class constants are properly defined.
    """
    assert LocalStorageAdapter.PREFIX is None
    assert "File written successfully" in LocalStorageAdapter.SUCCESS_WRITE_FILE
    assert "Error writing file" in LocalStorageAdapter.ERROR_WRITE_FILE
    assert "Error reading file" in LocalStorageAdapter.ERROR_READ_FILE
    assert "File already exists" in LocalStorageAdapter.FILE_EXIST_ERROR
    assert "File not found" in LocalStorageAdapter.WARNING_FILE_NOT_FOUND
    assert "Error listing files" in LocalStorageAdapter.ERROR_LIST_FILE
    assert "Error loading metric module" in LocalStorageAdapter.ERROR_LOADING_MODULE