"""
Tests for the FastAPI application.
"""

import pytest
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from entrypoints.api import app

client = TestClient(app)


def _create_mock_connector_entity():
    """Helper function to create a mock connector entity."""
    mock_connector_entity = MagicMock()
    mock_connector_entity.connector_adapter = "test_adapter"
    mock_connector_entity.model = "test_model"
    mock_connector_entity.model_endpoint = "test_endpoint"
    mock_connector_entity.params = {}
    mock_connector_entity.connector_pre_prompt = None
    mock_connector_entity.connector_post_prompt = None
    mock_connector_entity.system_prompt = None
    return mock_connector_entity


def _create_mock_connector_response():
    """Helper function to create a mock connector response."""
    from domain.entities.connector_response_entity import ConnectorResponseEntity
    return ConnectorResponseEntity(
        response="test response",
        context=[]
    )


def _create_mock_prompt_processor():
    """Helper function to create a mock prompt processor."""
    mock_prompt_processor_instance = AsyncMock()
    mock_prompt_processor_instance.process_prompts.return_value = ([], {"accuracy": 0.95})
    return mock_prompt_processor_instance


def _create_working_mock_connector_instance():
    """Helper function to create a working mock connector instance."""
    mock_connector_response = _create_mock_connector_response()
    mock_connector_instance = AsyncMock()
    mock_connector_instance.get_response = AsyncMock(return_value=mock_connector_response)
    mock_connector_instance.configure = MagicMock()
    return mock_connector_instance


def _create_failing_mock_connector_instance():
    """Helper function to create a failing mock connector instance."""
    failing_connector_instance = AsyncMock()
    failing_connector_instance.get_response = AsyncMock(side_effect=Exception("Connector failure"))
    failing_connector_instance.configure = MagicMock()
    return failing_connector_instance


def _create_benchmark_payload(test_name):
    """Helper function to create a standard benchmark payload."""
    return {
        "test_name": test_name,
        "dataset": "test_sample_dataset",
        "metric": "accuracy_adapter",
        "connector": "test_connector"
    }


def _assert_benchmark_started_successfully(response):
    """Helper function to assert benchmark started successfully."""
    assert response.status_code == 200
    assert response.json()["message"] == "Benchmark execution started successfully"


def _create_side_effect_functions(mock_connector_instance, mock_prompt_processor_instance):
    """Helper function to create side effect functions for module loading."""
    from domain.services.task_manager import TaskManager
    from domain.services.enums.module_types import ModuleTypes
    from domain.services.loader.module_loader import ModuleLoader
    
    original_load_module = TaskManager._load_module
    original_module_loader_load = ModuleLoader.load
    
    def load_module_side_effect(self, loader, name, *args, **kwargs):
        if loader.__name__ == 'FileLoader':
            return original_load_module(self, loader, name, *args, **kwargs)
        elif loader.__name__ == 'ModuleLoader' and args[1] == ModuleTypes.PROMPT_PROCESSOR:
            return (mock_prompt_processor_instance, "processor_id")
        elif loader.__name__ == 'ModuleLoader' and args[1] == ModuleTypes.CONNECTOR:
            return (mock_connector_instance, "connector_id")
        else:
            return original_load_module(self, loader, name, *args, **kwargs)
    
    def module_loader_side_effect(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR:
            return (mock_connector_instance, "connector_id")
        else:
            return original_module_loader_load(module_name, module_type)
    
    return load_module_side_effect, module_loader_side_effect


async def _wait_for_result_file_and_validate(absolute_result_path):
    """Helper function to wait for result file and validate JSON."""
    import json
    from tests.utils.report_validation.report_validation import validate_json
    
    max_wait = 15
    wait_interval = 0.2
    waited = 0
    
    while waited < max_wait:
        if absolute_result_path.exists():
            break
        await asyncio.sleep(wait_interval)
        waited += wait_interval
    
    assert absolute_result_path.exists(), (
        f"Result file not created after {waited:.1f}s. "
        f"Expected: {absolute_result_path}"
    )
    
    with open(absolute_result_path, 'r') as f:
        data = json.load(f)
    
    is_valid = validate_json(data)
    
    assert is_valid, (
        f"JSON output from API endpoint does not conform to expected schema (Schema1 or Schema2).\n"
        f"Data structure: {json.dumps(data, indent=2)[:1000]}..."
    )


async def _run_single_benchmark_and_wait(test_name, absolute_result_path):
    """Helper function to run a single benchmark and wait for its result file."""
    payload = _create_benchmark_payload(test_name)
    
    response = client.post("/api/run-benchmark", json=payload)
    _assert_benchmark_started_successfully(response)
    
    await _wait_for_result_file_and_validate(absolute_result_path)


@pytest.fixture
def cleanup_test_result_file():
    """
    Fixture to clean up test result files before and after the test.
    
    Yields the test file path, and cleans it up after the test completes.
    """
    from domain.services.app_config import AppConfig
    
    app_config = AppConfig()
    test_file_name = "test_benchmark_validation.json"
    result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = result_path.resolve()
    
    # Cleanup before test
    if result_path.exists():
        result_path.unlink()
    if os.path.exists(str(absolute_result_path)):
        os.remove(str(absolute_result_path))
    
    yield result_path, absolute_result_path
    
    # Cleanup after test
    if result_path.exists():
        result_path.unlink()
    if os.path.exists(str(absolute_result_path)):
        os.remove(str(absolute_result_path))


@pytest.fixture
def cleanup_test_result_files_concurrent():
    """
    Fixture to clean up multiple test result files for concurrent test.
    
    Yields a list of (result_path, absolute_result_path) tuples, and cleans them up after the test completes.
    """
    from domain.services.app_config import AppConfig
    
    app_config = AppConfig()
    test_file_names = [f"test_benchmark_concurrent_{i}.json" for i in range(5)]
    result_paths = []
    
    for test_file_name in test_file_names:
        result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
        absolute_result_path = result_path.resolve()
        
        # Cleanup before test
        if result_path.exists():
            result_path.unlink()
        if os.path.exists(str(absolute_result_path)):
            os.remove(str(absolute_result_path))
        
        result_paths.append((result_path, absolute_result_path))
    
    yield result_paths
    
    # Cleanup after test
    for result_path, absolute_result_path in result_paths:
        if result_path.exists():
            result_path.unlink()
        if os.path.exists(str(absolute_result_path)):
            os.remove(str(absolute_result_path))


@pytest.fixture
def cleanup_test_result_files_concurrent():
    """
    Fixture to clean up multiple test result files for concurrent test.
    
    Yields a list of (result_path, absolute_result_path) tuples, and cleans them up after the test completes.
    """
    from domain.services.app_config import AppConfig
    
    app_config = AppConfig()
    test_file_names = [f"test_benchmark_concurrent_{i}.json" for i in range(5)]
    result_paths = []
    
    for test_file_name in test_file_names:
        result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
        absolute_result_path = result_path.resolve()
        
        # Cleanup before test
        if result_path.exists():
            result_path.unlink()
        if os.path.exists(str(absolute_result_path)):
            os.remove(str(absolute_result_path))
        
        result_paths.append((result_path, absolute_result_path))
    
    yield result_paths
    
    # Cleanup after test
    for result_path, absolute_result_path in result_paths:
        if result_path.exists():
            result_path.unlink()
        if os.path.exists(str(absolute_result_path)):
            os.remove(str(absolute_result_path))


@pytest.fixture
def cleanup_test_result_file_recovery():
    """
    Fixture to clean up test result files for recovery test.
    
    Yields the test file path, and cleans it up after the test completes.
    """
    from domain.services.app_config import AppConfig
    
    app_config = AppConfig()
    test_file_name = "test_benchmark_recovery.json"
    result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = result_path.resolve()
    
    # Cleanup before test
    if result_path.exists():
        result_path.unlink()
    if os.path.exists(str(absolute_result_path)):
        os.remove(str(absolute_result_path))
    
    yield result_path, absolute_result_path
    
    # Cleanup after test
    if result_path.exists():
        result_path.unlink()
    if os.path.exists(str(absolute_result_path)):
        os.remove(str(absolute_result_path))


@patch('entrypoints.api.get_build_directory')
def test_root_endpoint(mock_get_build_dir):
    """Test the root endpoint."""
    # Mock the build directory to return a non-existent path so it returns JSON
    mock_build_dir = MagicMock()
    mock_index_file = MagicMock()
    mock_index_file.exists.return_value = False
    mock_build_dir.__truediv__.return_value = mock_index_file
    mock_get_build_dir.return_value = mock_build_dir
    
    response = client.get("/")
    assert response.status_code == 200
    # Should return JSON message since index.html doesn't exist
    assert response.json() == {"message": "Welcome to Moonshot CI/CD API"}


@patch('entrypoints.api.benchmark_service')
def test_bundles_endpoint(mock_benchmark_service):
    """Test the /api/bundles endpoint returns proper response structure."""
    # Mock the benchmark service to return test data
    mock_bundles = [
        {
            "name": "test_bundle",
            "description": "A test bundle",
            "tests": [
                {
                    "name": "test_1",
                    "metric": "accuracy_adapter",
                    "description": "Test description",
                    "dataset": "test_dataset"
                }
            ]
        }
    ]
    mock_benchmark_service.get_all_bundles.return_value = mock_bundles
    
    response = client.get("/api/bundles")
    assert response.status_code == 200
    
    data = response.json()
    assert "bundles" in data
    assert isinstance(data["bundles"], list)
    assert len(data["bundles"]) == 1
    
    # Verify bundle structure
    bundle = data["bundles"][0]
    assert "name" in bundle
    assert "description" in bundle
    assert "tests" in bundle
    assert isinstance(bundle["tests"], list)
    
    # Verify test structure
    test = bundle["tests"][0]
    assert "name" in test
    assert "metric" in test
    assert "description" in test
    assert "dataset" in test


@patch('entrypoints.api.get_build_directory')
def test_static_files_with_referer(mock_get_build_dir):
    """Test that static files are served when accessed with proper referer header."""
    # Mock the build directory
    mock_build_dir = MagicMock()
    mock_build_dir.resolve.return_value = Path("/mock/build/dir")
    mock_get_build_dir.return_value = mock_build_dir
    
    # Mock the requested file to not exist
    mock_requested_file = MagicMock()
    mock_requested_file.exists.return_value = False
    mock_requested_file.is_file.return_value = False
    mock_requested_file.is_dir.return_value = False
    mock_build_dir.__truediv__.return_value = mock_requested_file
    
    # Simulate a request with referer header (as if coming from the main page)
    response = client.get("/test-file.js", headers={"referer": "http://testserver/"})
    # Should return 404 for non-existent file, but not 403 (access denied)
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


@patch('entrypoints.api.get_build_directory')
def test_static_files_direct_access_blocked(mock_get_build_dir):
    """Test that direct access to static files is blocked."""
    # Mock the build directory
    mock_build_dir = MagicMock()
    mock_get_build_dir.return_value = mock_build_dir
    
    # Request without referer header (direct access)
    response = client.get("/test-file.js")
    assert response.status_code == 403
    assert "Direct access to static files is not allowed" in response.json()["detail"]


@patch('entrypoints.api.get_build_directory')
def test_static_files_cross_origin_blocked(mock_get_build_dir):
    """Test that cross-origin access to static files is blocked."""
    # Mock the build directory
    mock_build_dir = MagicMock()
    mock_get_build_dir.return_value = mock_build_dir
    
    # Request with referer from different origin
    response = client.get("/test-file.js", headers={"referer": "http://malicious-site.com/"})
    assert response.status_code == 403
    assert "Direct access to static files is not allowed" in response.json()["detail"]


@patch('entrypoints.api.get_build_directory')
def test_static_files_path_traversal_blocked(mock_get_build_dir):
    """Test that path traversal attempts are blocked."""
    # Mock the build directory
    mock_build_dir = MagicMock()
    mock_get_build_dir.return_value = mock_build_dir
    
    # Test path traversal attempt with URL-encoded .. 
    response = client.get("/test%2F..%2Fetc%2Fpasswd", headers={"referer": "http://testserver/"})
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


@patch('entrypoints.api.get_build_directory')
def test_next_js_static_files_with_referer(mock_get_build_dir):
    """Test that Next.js static files are served with proper referer."""
    # Mock the build directory
    mock_build_dir = MagicMock()
    mock_build_dir.resolve.return_value = Path("/mock/build/dir")
    mock_get_build_dir.return_value = mock_build_dir
    
    # Mock the requested file to not exist
    mock_requested_file = MagicMock()
    mock_requested_file.exists.return_value = False
    mock_requested_file.is_file.return_value = False
    mock_requested_file.is_dir.return_value = False
    mock_build_dir.__truediv__.return_value = mock_requested_file
    
    # Test Next.js static file access with referer
    response = client.get("/_next/static/test.js", headers={"referer": "http://testserver/"})
    # Should return 404 for non-existent file, but not 403 (access denied)
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


@patch('entrypoints.api.get_build_directory')
def test_next_js_static_files_direct_access_blocked(mock_get_build_dir):
    """Test that direct access to Next.js static files is blocked."""
    # Mock the build directory
    mock_build_dir = MagicMock()
    mock_get_build_dir.return_value = mock_build_dir
    
    # Direct access to Next.js static files without referer
    response = client.get("/_next/static/test.js")
    assert response.status_code == 403
    assert "Direct access to static files is not allowed" in response.json()["detail"]


@patch('entrypoints.api.BenchmarkExecutionService')
def test_run_benchmark_success(mock_service_class):
    """Test successful benchmark execution request."""
    # Create a mock service instance
    mock_service = MagicMock()
    mock_service.execute_benchmark = AsyncMock(return_value=None)
    mock_service_class.return_value = mock_service
    
    # Test payload
    payload = {
        "test_name": "test_benchmark_1",
        "dataset": "test_dataset",
        "metric": "accuracy_adapter",
        "connector": "my-gpt-4o"
    }
    
    response = client.post("/api/run-benchmark", json=payload)
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["test_name"] == "test_benchmark_1"
    assert data["message"] == "Benchmark execution started successfully"
    
    # Verify the service was called with correct parameters
    mock_service_class.assert_called_once()
    mock_service.execute_benchmark.assert_called_once_with(
        test_name="test_benchmark_1",
        dataset="test_dataset",
        metric="accuracy_adapter",
        connector="my-gpt-4o"
    )


@patch('entrypoints.api.BenchmarkExecutionService')
def test_run_benchmark_with_different_params(mock_service_class):
    """Test benchmark execution with different parameters."""
    # Create a mock service instance
    mock_service = MagicMock()
    mock_service.execute_benchmark = AsyncMock(return_value=None)
    mock_service_class.return_value = mock_service
    
    # Test payload with different values
    payload = {
        "test_name": "another_test",
        "dataset": "different_dataset",
        "metric": "custom_metric",
        "connector": "custom-connector"
    }
    
    response = client.post("/api/run-benchmark", json=payload)
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["test_name"] == "another_test"
    assert "successfully" in data["message"].lower()
    
    # Verify the service was called with the correct parameters
    mock_service.execute_benchmark.assert_called_once_with(
        test_name="another_test",
        dataset="different_dataset",
        metric="custom_metric",
        connector="custom-connector"
    )


@patch('entrypoints.api.BenchmarkExecutionService')
def test_run_benchmark_service_initialization_error(mock_service_class):
    """Test error handling when service initialization fails."""
    # Make the service class raise an exception on initialization
    mock_service_class.side_effect = Exception("Service initialization failed")
    
    payload = {
        "test_name": "test_benchmark",
        "dataset": "test_dataset",
        "metric": "accuracy_adapter",
        "connector": "my-gpt-4o"
    }
    
    response = client.post("/api/run-benchmark", json=payload)
    
    # Verify error response
    assert response.status_code == 500
    assert "Failed to start benchmark execution" in response.json()["detail"]


@patch('entrypoints.api.BenchmarkExecutionService')
def test_run_benchmark_execution_error(mock_service_class):
    """Test error handling when benchmark execution fails during task creation."""
    # Create a mock service instance that raises an error when execute_benchmark is called
    mock_service = MagicMock()
    mock_service.execute_benchmark = AsyncMock(side_effect=Exception("Execution failed"))
    mock_service_class.return_value = mock_service
    
    payload = {
        "test_name": "test_benchmark",
        "dataset": "test_dataset",
        "metric": "accuracy_adapter",
        "connector": "my-gpt-4o"
    }
    
    # Note: Since the endpoint uses asyncio.create_task and doesn't await,
    # the error might not be caught immediately. However, if there's an error
    # during task creation, it should be caught.
    # This test verifies the endpoint still returns a response
    response = client.post("/api/run-benchmark", json=payload)
    
    # The endpoint should still return 200 because it doesn't await the task
    # The error would be logged but not raised
    assert response.status_code == 200


def test_run_benchmark_invalid_payload():
    """Test benchmark endpoint with invalid/missing fields."""
    # Missing required fields
    payload = {
        "test_name": "test_benchmark"
        # Missing dataset, metric, connector
    }
    
    response = client.post("/api/run-benchmark", json=payload)
    
    # Should return 422 (Unprocessable Entity) for validation error
    assert response.status_code == 422


def test_run_benchmark_empty_payload():
    """Test benchmark endpoint with empty payload."""
    response = client.post("/api/run-benchmark", json={})
    
    # Should return 422 (Unprocessable Entity) for validation error
    assert response.status_code == 422


def test_run_benchmark_wrong_types():
    """Test benchmark endpoint with wrong data types."""
    payload = {
        "test_name": 123,  # Should be string
        "dataset": "test_dataset",
        "metric": "accuracy_adapter",
        "connector": "my-gpt-4o"
    }
    
    response = client.post("/api/run-benchmark", json=payload)
    
    # Should return 422 (Unprocessable Entity) for validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_run_benchmark_validates_json_output(cleanup_test_result_file):
    """
    Integration test: Run benchmark through API endpoint and validate JSON output.
    
    This test calls the API endpoint which runs the benchmark asynchronously.
    Only external dependencies (connector, prompt processor) are mocked to avoid API calls.
    Everything else runs for real: dataset loading, prompt generation, serialization, etc.
    """
    from domain.services.task_manager import TaskManager
    
    mock_connector_entity = _create_mock_connector_entity()
    mock_prompt_processor_instance = _create_mock_prompt_processor()
    mock_connector_instance = _create_working_mock_connector_instance()
    
    load_module_side_effect, module_loader_side_effect = _create_side_effect_functions(
        mock_connector_instance, mock_prompt_processor_instance
    )
    
    with patch.object(TaskManager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(TaskManager, '_load_module', side_effect=load_module_side_effect, autospec=True), \
         patch('domain.services.loader.module_loader.ModuleLoader.load', side_effect=module_loader_side_effect):
        
        result_path, absolute_result_path = cleanup_test_result_file
        payload = _create_benchmark_payload("test_benchmark_validation")
        
        response = client.post("/api/run-benchmark", json=payload)
        _assert_benchmark_started_successfully(response)
        
        await _wait_for_result_file_and_validate(absolute_result_path)


@pytest.mark.asyncio
async def test_run_benchmark_recovery_after_failure(cleanup_test_result_file_recovery):
    """
    Test recovery after failure: Run a failing test, then run a successful test.
    
    This test verifies that the system can recover from a failure and successfully
    run a benchmark test afterwards.
    """
    from domain.services.task_manager import TaskManager
    
    mock_connector_entity = _create_mock_connector_entity()
    mock_prompt_processor_instance = _create_mock_prompt_processor()
    
    result_path, absolute_result_path = cleanup_test_result_file_recovery
    payload = _create_benchmark_payload("test_benchmark_recovery")
    
    # Step 1: Run test with failing connector (unhappy path)
    failing_connector_instance = _create_failing_mock_connector_instance()
    
    load_module_side_effect_failing, module_loader_side_effect_failing = _create_side_effect_functions(
        failing_connector_instance, mock_prompt_processor_instance
    )
    
    with patch.object(TaskManager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(TaskManager, '_load_module', side_effect=load_module_side_effect_failing, autospec=True), \
         patch('domain.services.loader.module_loader.ModuleLoader.load', side_effect=module_loader_side_effect_failing):
        
        response = client.post("/api/run-benchmark", json=payload)
        assert response.status_code == 200
        
        await asyncio.sleep(2)
    
    # Step 2: Run test with working connector (happy path)
    working_connector_instance = _create_working_mock_connector_instance()
    
    load_module_side_effect_working, module_loader_side_effect_working = _create_side_effect_functions(
        working_connector_instance, mock_prompt_processor_instance
    )
    
    with patch.object(TaskManager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(TaskManager, '_load_module', side_effect=load_module_side_effect_working, autospec=True), \
         patch('domain.services.loader.module_loader.ModuleLoader.load', side_effect=module_loader_side_effect_working):
        
        response = client.post("/api/run-benchmark", json=payload)
        _assert_benchmark_started_successfully(response)
        
        await _wait_for_result_file_and_validate(absolute_result_path)


@pytest.mark.asyncio
async def test_run_multiple_benchmarks_concurrently(cleanup_test_result_files_concurrent):
    """
    Test running multiple benchmarks concurrently.
    
    This test runs 5 benchmark tests at the same time and verifies that all
    different JSON result files are created and validated.
    """
    from domain.services.task_manager import TaskManager
    
    mock_connector_entity = _create_mock_connector_entity()
    mock_prompt_processor_instance = _create_mock_prompt_processor()
    mock_connector_instance = _create_working_mock_connector_instance()
    
    load_module_side_effect, module_loader_side_effect = _create_side_effect_functions(
        mock_connector_instance, mock_prompt_processor_instance
    )
    
    result_paths = cleanup_test_result_files_concurrent
    test_names = [f"test_benchmark_concurrent_{i}" for i in range(5)]
    
    # Apply patches once at the test level for all concurrent benchmarks
    with patch.object(TaskManager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(TaskManager, '_load_module', side_effect=load_module_side_effect, autospec=True), \
         patch('domain.services.loader.module_loader.ModuleLoader.load', side_effect=module_loader_side_effect):
        
        # Run all 5 benchmarks concurrently
        tasks = []
        for i, (result_path, absolute_result_path) in enumerate(result_paths):
            task = _run_single_benchmark_and_wait(
                test_names[i],
                absolute_result_path
            )
            tasks.append(task)
        
        # Wait for all benchmarks to complete
        await asyncio.gather(*tasks)
    
    # Verify all result files exist and are valid
    for result_path, absolute_result_path in result_paths:
        assert absolute_result_path.exists(), (
            f"Result file not created: {absolute_result_path}"
        )
        await _wait_for_result_file_and_validate(absolute_result_path)
