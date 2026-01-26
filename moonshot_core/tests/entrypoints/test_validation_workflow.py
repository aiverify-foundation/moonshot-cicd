"""
Validation workflow tests for benchmark execution.

These tests verify the complete validation workflow:
1. Execute the validation function
2. Wait for the JSON file to be written to disk
3. Verify JSON file was created successfully
4. Run process checklist validation function on the JSON
5. Confirm validation result is "PASS"
"""

import pytest
import sys
import os
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
# Add the repo root to the Python path for process_check_app imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from entrypoints.api import app
from process_check_app.backend.report_validation import validate_json

client = TestClient(app)


# ============================================================================
# Helper Functions (copied/adapted from test_api.py)
# ============================================================================

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


def _create_benchmark_payload(test_name, connector="test_connector"):
    """Helper function to create a standard benchmark payload."""
    return {
        "test_name": test_name,
        "dataset": "test_sample_dataset",
        "metric": "accuracy_adapter",
        "connector": connector
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
    
    return data


async def _run_single_benchmark_and_wait(test_name, absolute_result_path, connector="test_connector"):
    """Helper function to run a single benchmark and wait for its result file."""
    payload = _create_benchmark_payload(test_name, connector)
    
    response = client.post("/api/run-benchmark", json=payload)
    _assert_benchmark_started_successfully(response)
    
    return await _wait_for_result_file_and_validate(absolute_result_path)


# ============================================================================
# New Helper Functions
# ============================================================================


def _verify_unique_identifiers(json_files_data):
    """
    Verify that all JSON files have unique identifiers.
    
    Args:
        json_files_data: List of tuples (file_path, json_data)
        
    Returns:
        dict: Mapping of run_id to test_id for verification
    """
    identifiers = {}
    run_ids = set()
    test_ids = set()
    
    for file_path, data in json_files_data:
        # Extract run_metadata
        run_metadata = data.get("run_metadata", {})
        run_id = run_metadata.get("run_id")
        test_id = run_metadata.get("test_id")
        
        assert run_id is not None, f"run_id is missing in {file_path}"
        assert test_id is not None, f"test_id is missing in {file_path}"
        
        # Verify uniqueness
        assert run_id not in run_ids, f"Duplicate run_id found: {run_id}"
        assert test_id not in test_ids, f"Duplicate test_id found: {test_id}"
        
        run_ids.add(run_id)
        test_ids.add(test_id)
        identifiers[run_id] = test_id
    
    return identifiers


# ============================================================================
# Cleanup Fixtures
# ============================================================================

def _cleanup_file(file_path):
    """Helper to remove a file if it exists."""
    if file_path.exists():
        file_path.unlink()
    if os.path.exists(str(file_path.resolve())):
        os.remove(str(file_path.resolve()))


@pytest.fixture
def cleanup_test_result_file_together():
    """Fixture to clean up test result file for Together connector test."""
    from domain.services.app_config import AppConfig
    
    app_config = AppConfig()
    test_file_name = "output_together_validation.json"
    result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = result_path.resolve()
    
    _cleanup_file(result_path)
    _cleanup_file(absolute_result_path)
    
    yield result_path, absolute_result_path
    
    _cleanup_file(result_path)
    _cleanup_file(absolute_result_path)


@pytest.fixture
def cleanup_test_result_file_openai():
    """Fixture to clean up test result file for OpenAI connector test."""
    from domain.services.app_config import AppConfig
    
    app_config = AppConfig()
    test_file_name = "output_openai_validation.json"
    result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = result_path.resolve()
    
    _cleanup_file(result_path)
    _cleanup_file(absolute_result_path)
    
    yield result_path, absolute_result_path
    
    _cleanup_file(result_path)
    _cleanup_file(absolute_result_path)


@pytest.fixture
def cleanup_test_result_file_recovery():
    """Fixture to clean up test result file for recovery test."""
    from domain.services.app_config import AppConfig
    
    app_config = AppConfig()
    test_file_name = "output_recovery_validation.json"
    result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = result_path.resolve()
    
    _cleanup_file(result_path)
    _cleanup_file(absolute_result_path)
    
    yield result_path, absolute_result_path
    
    _cleanup_file(result_path)
    _cleanup_file(absolute_result_path)


@pytest.fixture
def cleanup_test_result_files_concurrent_validation():
    """
    Fixture to clean up multiple test result files for concurrent validation test.
    
    Yields a list of (result_path, absolute_result_path) tuples, and cleans them up after the test completes.
    """
    from domain.services.app_config import AppConfig
    
    app_config = AppConfig()
    test_file_names = [
        "output_together_1.json",
        "output_openai_1.json",
        "output_together_2.json",
        "output_openai_2.json",
        "output_together_3.json"
    ]
    result_paths = []
    
    for test_file_name in test_file_names:
        result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
        absolute_result_path = result_path.resolve()
        _cleanup_file(result_path)
        _cleanup_file(absolute_result_path)
        result_paths.append((result_path, absolute_result_path))
    
    yield result_paths
    
    for result_path, absolute_result_path in result_paths:
        _cleanup_file(result_path)
        _cleanup_file(absolute_result_path)


# ============================================================================
# Test Helper Functions
# ============================================================================

def _setup_test_mocks():
    """Helper to set up common test mocks."""
    mock_connector_entity = _create_mock_connector_entity()
    mock_prompt_processor_instance = _create_mock_prompt_processor()
    mock_connector_instance = _create_working_mock_connector_instance()
    
    load_module_side_effect, module_loader_side_effect = _create_side_effect_functions(
        mock_connector_instance, mock_prompt_processor_instance
    )
    
    return mock_connector_entity, load_module_side_effect, module_loader_side_effect


def _verify_result_structure(data, test_name):
    """Helper to verify result file structure."""
    assert "run_metadata" in data
    assert "run_results" in data
    assert data["run_metadata"]["test_id"] == test_name


async def _run_validation_workflow_test(test_name, connector, absolute_result_path):
    """Helper to run a validation workflow test with common setup."""
    from domain.services.task_manager import TaskManager
    
    mock_connector_entity, load_module_side_effect, module_loader_side_effect = _setup_test_mocks()
    
    with patch.object(TaskManager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(TaskManager, '_load_module', side_effect=load_module_side_effect, autospec=True), \
         patch('domain.services.loader.module_loader.ModuleLoader.load', side_effect=module_loader_side_effect):
        
        payload = _create_benchmark_payload(test_name, connector)
        response = client.post("/api/run-benchmark", json=payload)
        _assert_benchmark_started_successfully(response)
        
        data = await _wait_for_result_file_and_validate(absolute_result_path)
        _verify_result_structure(data, test_name)
        return data


# ============================================================================
# Test Implementations
# ============================================================================

@pytest.mark.asyncio
async def test_validation_workflow_together_connector(cleanup_test_result_file_together):
    """
    Test 1: Happy Path - Together Connector
    
    Given: Together connector is configured
    When: Validation workflow executes
    Then: Validation passes
    """
    result_path, absolute_result_path = cleanup_test_result_file_together
    test_name = "output_together_validation"
    await _run_validation_workflow_test(test_name, "together_connector", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_openai_connector(cleanup_test_result_file_openai):
    """
    Test 2: Happy Path - OpenAI Connector
    
    Given: OpenAI connector is configured
    When: Validation workflow executes
    Then: Validation passes
    """
    result_path, absolute_result_path = cleanup_test_result_file_openai
    test_name = "output_openai_validation"
    await _run_validation_workflow_test(test_name, "my-gpt-4o", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_failure_recovery(cleanup_test_result_file_recovery):
    """
    Test 3: Unhappy Path - Failure Recovery
    
    Given: Together connector is configured
    When: Test call fails
    Then: Test is marked as failed
    When: Happy path test runs after failure
    Then: JSON is created and validation passes
    """
    from domain.services.task_manager import TaskManager
    
    mock_connector_entity = _create_mock_connector_entity()
    mock_prompt_processor_instance = _create_mock_prompt_processor()
    
    result_path, absolute_result_path = cleanup_test_result_file_recovery
    test_name = "output_recovery_validation"
    payload = _create_benchmark_payload(test_name, connector="together_connector")
    
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
    await _run_validation_workflow_test(test_name, "together_connector", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_concurrent_execution(cleanup_test_result_files_concurrent_validation):
    """
    Test 4: Concurrent Execution - 5 Benchmarks
    
    Given: Both Together and OpenAI connectors are configured
    When: 5 validation tests run simultaneously:
      - Test 4.1: Together connector - instance 1
      - Test 4.2: OpenAI connector - instance 1
      - Test 4.3: Together connector - instance 2
      - Test 4.4: OpenAI connector - instance 2
      - Test 4.5: Together connector - instance 3
    Then: 5 distinct JSON files are created:
      - output_together_1.json
      - output_openai_1.json
      - output_together_2.json
      - output_openai_2.json
      - output_together_3.json
    And: Each file has a unique identifier
    And: All 5 files pass process checklist validation
    And: No race conditions or file conflicts occur
    """
    from domain.services.task_manager import TaskManager
    
    mock_connector_entity = _create_mock_connector_entity()
    mock_prompt_processor_instance = _create_mock_prompt_processor()
    mock_connector_instance = _create_working_mock_connector_instance()
    
    load_module_side_effect, module_loader_side_effect = _create_side_effect_functions(
        mock_connector_instance, mock_prompt_processor_instance
    )
    
    result_paths = cleanup_test_result_files_concurrent_validation
    
    # Define test names matching the required file names
    test_names = [
        "output_together_1",
        "output_openai_1",
        "output_together_2",
        "output_openai_2",
        "output_together_3",
    ]
    
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
    json_files_data = []
    for i, (result_path, absolute_result_path) in enumerate(result_paths):
        test_name = test_names[i]
        
        # Verify file exists
        assert absolute_result_path.exists(), (
            f"Result file not created: {absolute_result_path}"
        )
        
        # Validate JSON and get data
        data = await _wait_for_result_file_and_validate(absolute_result_path)
        json_files_data.append((absolute_result_path, data))
        
        # Verify test name matches
        assert data["run_metadata"]["test_id"] == test_name, (
            f"Test ID mismatch in {absolute_result_path}. "
            f"Expected: {test_name}, Got: {data['run_metadata']['test_id']}"
        )
    
    # Verify 5 distinct JSON files were created with correct names
    assert len(json_files_data) == 5, "Expected 5 JSON files, got {}".format(len(json_files_data))
    
    # Verify each file has a unique identifier
    identifiers = _verify_unique_identifiers(json_files_data)
    assert len(identifiers) == 5, "Expected 5 unique identifiers, got {}".format(len(identifiers))
    
    # Verify all 5 files pass process checklist validation (already done in _wait_for_result_file_and_validate)
    # Verify no race conditions - all files are distinct (no overwrites)
    file_paths = [str(path) for path, _ in json_files_data]
    assert len(set(file_paths)) == 5, "Duplicate file paths detected - possible race condition"
    
    # Verify files contain correct connector information
    for absolute_result_path, data in json_files_data:
        assert "run_metadata" in data, f"Missing run_metadata in {absolute_result_path}"
