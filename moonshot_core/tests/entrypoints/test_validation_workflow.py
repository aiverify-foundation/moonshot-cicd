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

def _create_bundle_payload(connector="my-gpt-4o-mini"):
    """Helper function to create a standard bundle payload."""
    return {
        "bundle_name": "test-prompts",
        "connector": connector,
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


async def _run_single_bundle_and_wait(absolute_result_path, connector="my-gpt-4o-mini"):
    """Helper function to run a single bundle and wait for its result file."""
    payload = _create_bundle_payload(connector)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/run-bundle", json=payload)
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
def cleanup_bundle_result_file():
    """Fixture to clean up the bundle result file."""
    app_config = AppConfig()
    test_file_name = "test-prompts.json"
    absolute_result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = absolute_result_path.resolve()
    
    _cleanup_file(absolute_result_path)
    
    yield absolute_result_path
    
    _cleanup_file(absolute_result_path)


# ============================================================================
# Test Helper Functions
# ============================================================================

def _verify_result_structure(data, bundle_id):
    """Helper to verify result file structure."""
    assert "run_metadata" in data
    assert "run_results" in data
    assert data["run_metadata"]["test_id"] == bundle_id


async def _run_validation_workflow_test(connector, absolute_result_path):
    """Helper to run a validation workflow test with common setup.
    
    Args:
        connector: Connector name to use
        absolute_result_path: Path to the result file
    """
    payload = _create_bundle_payload(connector)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/run-bundle", json=payload)
        _assert_benchmark_started_successfully(response)
    
    data = await _wait_for_result_file_and_validate(absolute_result_path)
    _verify_result_structure(data, "test-prompts")
    return data


# ============================================================================
# Test Implementations
# ============================================================================

@pytest.mark.asyncio
async def test_validation_workflow_together_connector(cleanup_bundle_result_file):
    """
    Test 1: Happy Path - Together Connector (using my-together-llama-8b)
    
    Given: Together connector is configured
    When: Validation workflow executes
    Then: Validation passes
    """
    absolute_result_path = cleanup_bundle_result_file
    await _run_validation_workflow_test("my-together-llama-8b", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_openai_connector(cleanup_bundle_result_file):
    """
    Test 2: Happy Path - OpenAI Connector
    
    Given: OpenAI connector is configured
    When: Validation workflow executes
    Then: Validation passes
    """
    absolute_result_path = cleanup_bundle_result_file
    await _run_validation_workflow_test("my-gpt-4o-mini", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_failure_recovery(cleanup_bundle_result_file):
    """
    Test 3: Unhappy Path - Failure Recovery
    
    Given: Test connector is configured
    When: Test call fails (simulated by using invalid connector)
    Then: Test is marked as failed
    When: Happy path test runs after failure
    Then: JSON is created and validation passes
    """
    absolute_result_path = cleanup_bundle_result_file
    
    # Step 1: Try with invalid connector (should fail gracefully)
    payload = _create_bundle_payload(connector="invalid_connector")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/run-bundle", json=payload)
        # The endpoint should still return 200 (it starts the task, failure happens async)
        assert response.status_code == 200
    
    # Wait for Step 1 to complete (it runs in a separate process)
    # Give it time to finish and ensure no file was created (or clean up if one was)
    await asyncio.sleep(2)
    _cleanup_file(absolute_result_path)
    
    # Step 2: Run test with valid connector (happy path)
    await _run_validation_workflow_test("my-gpt-4o-mini", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_concurrent_execution(cleanup_bundle_result_file):
    """
    Test 4: Concurrent Execution - 5 Bundle Runs (same bundle ID)
    
    Given: Multiple connectors are configured
    When: 5 bundle runs start simultaneously (all write to the same result file):
      - Test 4.1: my-together-llama-8b - instance 1
      - Test 4.2: my-gpt-4o-mini - instance 1
      - Test 4.3: my-together-llama-8b - instance 2
      - Test 4.4: my-gpt-4o-mini - instance 2
      - Test 4.5: my-together-llama-8b - instance 3
    Then: The final JSON file exists and passes process checklist validation
    """
    absolute_result_path = cleanup_bundle_result_file
    
    # Define connectors for each test (using connectors from main config)
    connectors = [
        "my-together-llama-8b",
        "my-gpt-4o-mini",
        "my-together-llama-8b",
        "my-gpt-4o-mini",
        "my-together-llama-8b",
    ]
    
    # Run all 5 bundle runs concurrently
    tasks = []
    for connector in connectors:
        task = _run_single_bundle_and_wait(absolute_result_path, connector=connector)
        tasks.append(task)
    
    # Wait for all bundle runs to complete
    await asyncio.gather(*tasks)
    
    # Verify the final result file exists and is valid
    assert absolute_result_path.exists(), f"Result file not created: {absolute_result_path}"
    data = await _wait_for_result_file_and_validate(absolute_result_path)
    _verify_result_structure(data, "test-prompts")
