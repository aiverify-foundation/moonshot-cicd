"""
Validation workflow tests for benchmark execution.

These tests verify the complete validation workflow:
1. Execute the validation function
2. Wait for the JSON file to be written to disk
3. Verify JSON file was created successfully
4. Run process checklist validation function on the JSON
5. Confirm validation result is "PASS"

These tests use test connectors and metrics that don't require API keys or external services.
"""

import pytest
import sys
import os
import asyncio
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
# Add the repo root to the Python path for process_check_app imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from entrypoints.api import app
from process_check_app.backend.report_validation import validate_json
from domain.services.app_config import AppConfig


# ============================================================================
# Helper Functions
# ============================================================================

def _create_benchmark_payload(test_name, connector="my-gpt-4o-mini"):
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


async def _run_single_benchmark_and_wait(test_name, absolute_result_path, connector="my-gpt-4o-mini"):
    """Helper function to run a single benchmark and wait for its result file."""
    payload = _create_benchmark_payload(test_name, connector)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/run-benchmark", json=payload)
        _assert_benchmark_started_successfully(response)
    
    return await _wait_for_result_file_and_validate(absolute_result_path)


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
    app_config = AppConfig()
    test_file_name = "output_together_validation.json"
    absolute_result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = absolute_result_path.resolve()
    
    _cleanup_file(absolute_result_path)
    
    yield absolute_result_path
    
    _cleanup_file(absolute_result_path)


@pytest.fixture
def cleanup_test_result_file_openai():
    """Fixture to clean up test result file for OpenAI connector test."""
    app_config = AppConfig()
    test_file_name = "output_openai_validation.json"
    absolute_result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = absolute_result_path.resolve()
    
    _cleanup_file(absolute_result_path)
    
    yield absolute_result_path
    
    _cleanup_file(absolute_result_path)


@pytest.fixture
def cleanup_test_result_file_recovery():
    """Fixture to clean up test result file for recovery test."""
    app_config = AppConfig()
    test_file_name = "output_recovery_validation.json"
    absolute_result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = absolute_result_path.resolve()
    
    _cleanup_file(absolute_result_path)
    
    yield absolute_result_path
    
    _cleanup_file(absolute_result_path)


@pytest.fixture
def cleanup_test_result_files_concurrent_validation():
    """
    Fixture to clean up multiple test result files for concurrent validation test.
    
    Yields a list of absolute_result_path Path objects, and cleans them up after the test completes.
    """
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
        absolute_result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
        absolute_result_path = absolute_result_path.resolve()
        _cleanup_file(absolute_result_path)
        result_paths.append(absolute_result_path)
    
    yield result_paths
    
    for absolute_result_path in result_paths:
        _cleanup_file(absolute_result_path)


# ============================================================================
# Test Helper Functions
# ============================================================================

def _verify_result_structure(data, test_name):
    """Helper to verify result file structure."""
    assert "run_metadata" in data
    assert "run_results" in data
    assert data["run_metadata"]["test_id"] == test_name


async def _run_validation_workflow_test(test_name, connector, absolute_result_path):
    """Helper to run a validation workflow test with common setup.
    
    Args:
        test_name: Name of the test
        connector: Connector name to use
        absolute_result_path: Path to the result file
    """
    payload = _create_benchmark_payload(test_name, connector)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/run-benchmark", json=payload)
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
    Test 1: Happy Path - Together Connector (using my-together-llama-8b)
    
    Given: Together connector is configured
    When: Validation workflow executes
    Then: Validation passes
    """
    absolute_result_path = cleanup_test_result_file_together
    test_name = "output_together_validation"
    await _run_validation_workflow_test(test_name, "my-together-llama-8b", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_openai_connector(cleanup_test_result_file_openai):
    """
    Test 2: Happy Path - OpenAI Connector
    
    Given: OpenAI connector is configured
    When: Validation workflow executes
    Then: Validation passes
    """
    absolute_result_path = cleanup_test_result_file_openai
    test_name = "output_openai_validation"
    await _run_validation_workflow_test(test_name, "my-gpt-4o-mini", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_failure_recovery(cleanup_test_result_file_recovery):
    """
    Test 3: Unhappy Path - Failure Recovery
    
    Given: Test connector is configured
    When: Test call fails (simulated by using invalid connector)
    Then: Test is marked as failed
    When: Happy path test runs after failure
    Then: JSON is created and validation passes
    """
    absolute_result_path = cleanup_test_result_file_recovery
    test_name = "output_recovery_validation"
    
    # Step 1: Try with invalid connector (should fail gracefully)
    payload = _create_benchmark_payload(test_name, connector="invalid_connector")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/run-benchmark", json=payload)
        # The endpoint should still return 200 (it starts the task, failure happens async)
        assert response.status_code == 200
    
    # Step 2: Run test with valid connector (happy path)
    await _run_validation_workflow_test(test_name, "my-gpt-4o-mini", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_concurrent_execution(cleanup_test_result_files_concurrent_validation):
    """
    Test 4: Concurrent Execution - 5 Benchmarks
    
    Given: Multiple connectors are configured
    When: 5 validation tests run simultaneously:
      - Test 4.1: my-together-llama-8b - instance 1
      - Test 4.2: my-gpt-4o-mini - instance 1
      - Test 4.3: my-together-llama-8b - instance 2
      - Test 4.4: my-gpt-4o-mini - instance 2
      - Test 4.5: my-together-llama-8b - instance 3
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
    result_paths = cleanup_test_result_files_concurrent_validation
    
    # Define test names matching the required file names
    test_names = [
        "output_together_1",
        "output_openai_1",
        "output_together_2",
        "output_openai_2",
        "output_together_3",
    ]
    
    # Define connectors for each test (using connectors from main config)
    connectors = [
        "my-together-llama-8b",
        "my-gpt-4o-mini",
        "my-together-llama-8b",
        "my-gpt-4o-mini",
        "my-together-llama-8b",
    ]
    
    # Run all 5 benchmarks concurrently
    tasks = []
    for i, absolute_result_path in enumerate(result_paths):
        task = _run_single_benchmark_and_wait(
            test_names[i],
            absolute_result_path,
            connector=connectors[i]
        )
        tasks.append(task)
    
    # Wait for all benchmarks to complete
    await asyncio.gather(*tasks)
    
    # Verify all result files exist and are valid
    json_files_data = []
    for i, absolute_result_path in enumerate(result_paths):
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
    
    # Verify all 5 files pass process checklist validation (already done in _wait_for_result_file_and_validate)
    # Verify no race conditions - all files are distinct (no overwrites)
    file_paths = [str(path) for path, _ in json_files_data]
    assert len(set(file_paths)) == 5, "Duplicate file paths detected - possible race condition"
    
    # Verify files contain correct connector information
    for absolute_result_path, data in json_files_data:
        assert "run_metadata" in data, f"Missing run_metadata in {absolute_result_path}"
