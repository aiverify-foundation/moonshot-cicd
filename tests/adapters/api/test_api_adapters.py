import pytest
import os
import tempfile
import shutil
from unittest.mock import AsyncMock, patch, MagicMock, call
from adapters.api.api_adapter import ApiAdapter


@pytest.fixture
def api_adapter():
    """
    Create an ApiAdapter instance for testing.
    
    Returns:
        ApiAdapter: A fresh ApiAdapter instance for testing.
    """
    return ApiAdapter()


@pytest.fixture
def temp_directory():
    """
    Create a temporary directory for testing.
    
    Yields:
        str: Path to the temporary directory.
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_initialization(api_adapter):
    """
    Test that ApiAdapter initializes correctly.
    
    Args:
        api_adapter: ApiAdapter instance fixture.
    """
    assert api_adapter.app_config is not None


@patch('adapters.api.api_adapter.StorageProviderFactory.get_adapter')
def test_check_run_id_exist(mock_get_adapter, api_adapter):
    """
    Test the _check_run_id_exist method with different scenarios.
    
    Args:
        mock_get_adapter: Mocked storage provider factory.
        api_adapter: ApiAdapter instance fixture.
    """
    # Mock the storage adapter
    mock_storage_adapter = MagicMock()
    mock_get_adapter.return_value = mock_storage_adapter

    # Test when run_id exists
    mock_storage_adapter.exists.return_value = True
    assert api_adapter._check_run_id_exist('existing_run_id') is True
    
    # Verify the correct file path is constructed
    expected_path = f"{api_adapter.app_config.DEFAULT_RESULTS_PATH}/existing_run_id.json"
    mock_get_adapter.assert_called_with(expected_path)
    mock_storage_adapter.exists.assert_called_with(expected_path)

    # Test when run_id does not exist
    mock_storage_adapter.exists.return_value = False
    assert api_adapter._check_run_id_exist('non_existing_run_id') is False


@patch('adapters.api.api_adapter.AppConfig')
def test_delete_all_in_temp_folder_folder_not_exist(mock_app_config, api_adapter, temp_directory):
    """
    Test delete_all_in_temp_folder when folder doesn't exist.
    
    Args:
        mock_app_config: Mocked app configuration.
        api_adapter: ApiAdapter instance fixture.
        temp_directory: Temporary directory fixture.
    """
    non_existent_path = os.path.join(temp_directory, 'non_existent')
    mock_app_config.DEFAULT_TEMP_PATH = non_existent_path
    
    # Should not raise an exception when folder doesn't exist
    api_adapter.delete_all_in_temp_folder()


@patch('adapters.api.api_adapter.AppConfig')
def test_delete_all_in_temp_folder_success(mock_app_config, api_adapter, temp_directory):
    """
    Test successful deletion of all contents in temp folder.
    
    Args:
        mock_app_config: Mocked app configuration.
        api_adapter: ApiAdapter instance fixture.
        temp_directory: Temporary directory fixture.
    """
    mock_app_config.DEFAULT_TEMP_PATH = temp_directory
    
    # Create test files and directories
    test_file = os.path.join(temp_directory, 'test_file.txt')
    test_dir = os.path.join(temp_directory, 'test_dir')
    test_subfile = os.path.join(test_dir, 'subfile.txt')
    
    with open(test_file, 'w') as f:
        f.write('test content')
    
    os.makedirs(test_dir)
    with open(test_subfile, 'w') as f:
        f.write('sub content')
    
    # Verify files exist before deletion
    assert os.path.exists(test_file)
    assert os.path.exists(test_dir)
    assert os.path.exists(test_subfile)
    
    # Call the method
    api_adapter.delete_all_in_temp_folder()
    
    # Verify all contents are deleted but folder itself exists
    assert os.path.exists(temp_directory)
    assert not os.path.exists(test_file)
    assert not os.path.exists(test_dir)


@patch('adapters.api.api_adapter.AppConfig')
@patch('adapters.api.api_adapter.os.unlink')
def test_delete_all_in_temp_folder_unlink_error(mock_unlink, mock_app_config, api_adapter, temp_directory):
    """
    Test delete_all_in_temp_folder when unlink fails.
    
    Args:
        mock_unlink: Mocked os.unlink function.
        mock_app_config: Mocked app configuration.
        api_adapter: ApiAdapter instance fixture.
        temp_directory: Temporary directory fixture.
    """
    mock_app_config.DEFAULT_TEMP_PATH = temp_directory
    mock_unlink.side_effect = OSError("Permission denied")
    
    # Create a test file
    test_file = os.path.join(temp_directory, 'test_file.txt')
    with open(test_file, 'w') as f:
        f.write('test content')
    
    # Should raise OSError when unlink fails
    with pytest.raises(OSError, match="Failed to delete"):
        api_adapter.delete_all_in_temp_folder()


@pytest.mark.asyncio
@patch('adapters.api.api_adapter.TaskManager')
@patch('adapters.api.api_adapter.ApiAdapter._check_run_id_exist')
@patch('adapters.api.api_adapter.ApiAdapter.delete_all_in_temp_folder')
async def test_create_run_test_success(mock_delete_temp, mock_check_run_id_exist, mock_task_manager, api_adapter):
    """
    Test successful execution of create_run_test.
    
    Args:
        mock_delete_temp: Mocked delete_all_in_temp_folder method.
        mock_check_run_id_exist: Mocked _check_run_id_exist method.
        mock_task_manager: Mocked TaskManager class.
        api_adapter: ApiAdapter instance fixture.
    """
    # Mock the task manager
    mock_task_manager_instance = mock_task_manager.return_value
    mock_task_manager_instance.run_test = AsyncMock()

    # Test when run_id does not exist (normal execution)
    mock_check_run_id_exist.return_value = False
    
    with patch('adapters.api.api_adapter.logger') as mock_logger:
        await api_adapter.create_run_test('new_run_id', 'test_config_id', 'connector_config')
        
        # Verify run_test was called with correct parameters
        mock_task_manager_instance.run_test.assert_awaited_once_with(
            'new_run_id', 'test_config_id', 'connector_config', 
            'asyncio_prompt_processor_adapter', None
        )
        
        # Verify success message was logged
        mock_logger.info.assert_called_with(
            api_adapter.TEST_CONFIG_SUCCESS_MSG.format(run_id='new_run_id')
        )
        
        # Verify cleanup was called
        mock_delete_temp.assert_called_once()


@pytest.mark.asyncio
@patch('adapters.api.api_adapter.TaskManager')
@patch('adapters.api.api_adapter.ApiAdapter._check_run_id_exist')
@patch('adapters.api.api_adapter.ApiAdapter.delete_all_in_temp_folder')
async def test_create_run_test_with_callback(mock_delete_temp, mock_check_run_id_exist, mock_task_manager, api_adapter):
    """
    Test create_run_test with custom callback function.
    
    Args:
        mock_delete_temp: Mocked delete_all_in_temp_folder method.
        mock_check_run_id_exist: Mocked _check_run_id_exist method.
        mock_task_manager: Mocked TaskManager class.
        api_adapter: ApiAdapter instance fixture.
    """
    mock_task_manager_instance = mock_task_manager.return_value
    mock_task_manager_instance.run_test = AsyncMock()
    mock_check_run_id_exist.return_value = False
    
    callback_fn = MagicMock()
    custom_prompt_processor = "custom_processor"
    
    await api_adapter.create_run_test(
        'test_run_id', 'test_config_id', 'connector_config', 
        custom_prompt_processor, callback_fn
    )
    
    # Verify run_test was called with custom parameters
    mock_task_manager_instance.run_test.assert_awaited_once_with(
        'test_run_id', 'test_config_id', 'connector_config', 
        custom_prompt_processor, callback_fn
    )


@pytest.mark.asyncio
@patch('adapters.api.api_adapter.TaskManager')
@patch('adapters.api.api_adapter.ApiAdapter._check_run_id_exist')
@patch('adapters.api.api_adapter.ApiAdapter.delete_all_in_temp_folder')
async def test_create_run_test_file_exists_error(mock_delete_temp, mock_check_run_id_exist, mock_task_manager, api_adapter):
    """
    Test create_run_test when run_id already exists.
    
    Args:
        mock_delete_temp: Mocked delete_all_in_temp_folder method.
        mock_check_run_id_exist: Mocked _check_run_id_exist method.
        mock_task_manager: Mocked TaskManager class.
        api_adapter: ApiAdapter instance fixture.
    """
    mock_check_run_id_exist.return_value = True
    
    with patch('adapters.api.api_adapter.logger') as mock_logger:
        await api_adapter.create_run_test('existing_run_id', 'test_config_id', 'connector_config')
        
        # Verify error message was logged
        mock_logger.error.assert_called_with(
            api_adapter.FILE_EXIST_ERROR.format(run_id='existing_run_id')
        )
        
        # Verify TaskManager was not called
        mock_task_manager.assert_not_called()
        
        # Verify cleanup was still called
        mock_delete_temp.assert_called_once()


@pytest.mark.asyncio
@patch('adapters.api.api_adapter.TaskManager')
@patch('adapters.api.api_adapter.ApiAdapter._check_run_id_exist')
@patch('adapters.api.api_adapter.ApiAdapter.delete_all_in_temp_folder')
async def test_create_run_test_general_exception(mock_delete_temp, mock_check_run_id_exist, mock_task_manager, api_adapter):
    """
    Test create_run_test when a general exception occurs.
    
    Args:
        mock_delete_temp: Mocked delete_all_in_temp_folder method.
        mock_check_run_id_exist: Mocked _check_run_id_exist method.
        mock_task_manager: Mocked TaskManager class.
        api_adapter: ApiAdapter instance fixture.
    """
    mock_task_manager_instance = mock_task_manager.return_value
    mock_task_manager_instance.run_test = AsyncMock()
    mock_check_run_id_exist.return_value = False
    
    # Make run_test raise an exception
    test_exception = Exception("Test Exception")
    mock_task_manager_instance.run_test.side_effect = test_exception
    
    with patch('adapters.api.api_adapter.logger') as mock_logger:
        await api_adapter.create_run_test('new_run_id', 'test_config_id', 'connector_config')
        
        # Verify error message was logged
        mock_logger.error.assert_called_with(
            api_adapter.RUN_TEST_ERROR_MSG.format(error=test_exception)
        )
        
        # Verify cleanup was still called
        mock_delete_temp.assert_called_once()


@pytest.mark.asyncio
@patch('adapters.api.api_adapter.TaskManager')
@patch('adapters.api.api_adapter.ApiAdapter._check_run_id_exist')
@patch('adapters.api.api_adapter.ApiAdapter.delete_all_in_temp_folder')
async def test_create_run_test_cleanup_always_called(mock_delete_temp, mock_check_run_id_exist, mock_task_manager, api_adapter):
    """
    Test that cleanup is always called regardless of success or failure.
    
    Args:
        mock_delete_temp: Mocked delete_all_in_temp_folder method.
        mock_check_run_id_exist: Mocked _check_run_id_exist method.
        mock_task_manager: Mocked TaskManager class.
        api_adapter: ApiAdapter instance fixture.
    """
    mock_task_manager_instance = mock_task_manager.return_value
    mock_task_manager_instance.run_test = AsyncMock()
    
    # Test scenarios: success, FileExistsError, and general exception
    scenarios = [
        (False, None),  # Success case
        (True, None),   # FileExistsError case
        (False, Exception("Test error"))  # General exception case
    ]
    
    for run_id_exists, exception in scenarios:
        mock_delete_temp.reset_mock()
        mock_check_run_id_exist.return_value = run_id_exists
        
        if exception:
            mock_task_manager_instance.run_test.side_effect = exception
        else:
            mock_task_manager_instance.run_test.side_effect = None
        
        with patch('adapters.api.api_adapter.logger'):
            await api_adapter.create_run_test('test_run_id', 'test_config_id', 'connector_config')
        
        # Verify cleanup was called in all scenarios
        mock_delete_temp.assert_called_once()


def test_logging_constants(api_adapter):
    """
    Test that all logging message constants are defined.
    
    Args:
        api_adapter: ApiAdapter instance fixture.
    """
    assert hasattr(api_adapter, 'BENCHMARK_INFO_MSG')
    assert hasattr(api_adapter, 'CONNECTOR_CONFIG_NOT_FOUND_MSG')
    assert hasattr(api_adapter, 'BENCHMARK_SUCCESS_MSG')
    assert hasattr(api_adapter, 'BENCHMARK_ERROR_MSG')
    assert hasattr(api_adapter, 'SCAN_INFO_MSG')
    assert hasattr(api_adapter, 'SCAN_SUCCESS_MSG')
    assert hasattr(api_adapter, 'SCAN_ERROR_MSG')
    assert hasattr(api_adapter, 'TEST_CONFIG_SUCCESS_MSG')
    assert hasattr(api_adapter, 'RUN_TEST_ERROR_MSG')
    assert hasattr(api_adapter, 'FILE_EXIST_ERROR')
    
    # Verify they are strings and contain placeholders
    assert isinstance(api_adapter.FILE_EXIST_ERROR, str)
    assert '{run_id}' in api_adapter.FILE_EXIST_ERROR
    assert isinstance(api_adapter.TEST_CONFIG_SUCCESS_MSG, str)
    assert '{run_id}' in api_adapter.TEST_CONFIG_SUCCESS_MSG
