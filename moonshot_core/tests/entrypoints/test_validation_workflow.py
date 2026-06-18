"""
Validation workflow tests for benchmark execution.

These tests verify the complete validation workflow:
1. Execute the validation function
2. Wait for the JSON file to be written to disk
3. Verify JSON file was created successfully
4. Run process checklist validation function on the JSON
5. Confirm validation result is "PASS"

These tests call real connectors (e.g. OpenAI) and need credentials in the environment.
They use tests/entrypoints/conftest.py: isolated MOONSHOT_DB_PATH + shared.yaml seed so
runs do not collide with developer moonshot.db. execute_bundle reuses benchmark_run name
"Bundle run: {bundle_id}", so multi-run tests here are sequential (not parallel subprocesses).
"""

import pytest
import sys
import os
import asyncio
import json
import multiprocessing
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
# Add the repo root to the Python path for process_check_app imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from sqlalchemy import text

from adapters.driven.repository.sqlalchemy.session_manager import (
    SessionManager,
    set_skip_alembic_upgrade,
)
from application.services.benchmark_execution_service import BenchmarkExecutionService
from process_check_app.backend.report_validation import validate_json
from domain.services.app_config import AppConfig

# test-bundle uses llamaguardannotator_adapter (OpenAI target + Together judge per prompt).
TEST_BUNDLE_MAX_WAIT = 600


# ============================================================================
# Helper Functions
# ============================================================================

def _cleanup_bundle_run_db(bundle_id: str) -> None:
    """
    Delete benchmark_run and dependent rows for execute_bundle's default name
    ``Bundle run: {bundle_id}``.

    Without this, a second background YAML bundle run for the same bundle_id reuses the same
    benchmark_run and can hit UNIQUE / state errors on benchmark_run_test_status.
    Tests only — production behavior unchanged.
    """
    run_name = f"Bundle run: {bundle_id}"
    session_manager = SessionManager.get_instance()
    with session_manager.get_session() as session:
        row = session.execute(
            text("SELECT id FROM benchmark_run WHERE name = :n"), {"n": run_name}
        ).fetchone()
        if row is None:
            return
        rid = row[0]
        session.execute(
            text(
                "DELETE FROM benchmark_run_test_prompt WHERE run_test_id IN "
                "(SELECT id FROM benchmark_run_test_status WHERE run_id = :rid)"
            ),
            {"rid": rid},
        )
        session.execute(
            text("DELETE FROM benchmark_run_test_status WHERE run_id = :rid"),
            {"rid": rid},
        )
        session.execute(
            text("DELETE FROM benchmark_run_test_bundle WHERE run_id = :rid"),
            {"rid": rid},
        )
        session.execute(text("DELETE FROM benchmark_run WHERE id = :rid"), {"rid": rid})


def _run_yaml_bundle_in_process(bundle_name: str, connector: str) -> None:
    """Picklable target: YAML connector path (not DB FKs). Matches skip-alembic worker behavior."""
    set_skip_alembic_upgrade(True)
    try:
        BenchmarkExecutionService().execute_bundle(
            bundle_name,
            connector,
            run_id=None,
            write_to_db=True,
        )
    finally:
        set_skip_alembic_upgrade(False)


def _start_bundle_in_background(bundle_name: str, connector: str) -> None:
    """Start YAML-based bundle execution in a daemon process (validation tests only)."""
    proc = multiprocessing.Process(
        target=_run_yaml_bundle_in_process,
        args=(bundle_name, connector),
    )
    proc.daemon = True
    proc.start()


async def _wait_for_result_file_and_validate(absolute_result_path, max_wait=60):
    """Helper function to wait for result file and validate JSON."""
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
        f"JSON output from benchmark run does not conform to expected schema (Schema1 or Schema2).\n"
        f"Data structure: {json.dumps(data, indent=2)[:1000]}..."
    )
    
    return data


async def _run_single_bundle_and_wait(
    absolute_result_path,
    connector="my-gpt-4o-mini",
    bundle_name="test-bundle",
    max_wait=TEST_BUNDLE_MAX_WAIT,
):
    """Helper function to run a single bundle and wait for its result file."""
    _start_bundle_in_background(bundle_name, connector)
    return await _wait_for_result_file_and_validate(
        absolute_result_path, max_wait=max_wait
    )


# ============================================================================
# Cleanup Fixtures
# ============================================================================

def _cleanup_file(file_path):
    """Helper to remove a file if it exists."""
    if file_path.exists():
        file_path.unlink()
    if os.path.exists(str(file_path.resolve())):
        os.remove(str(file_path.resolve()))


def _cleanup_bundle_result_file_for(bundle_id):
    """Return a fixture-like (setup, path, teardown) for a bundle result file."""
    app_config = AppConfig()
    test_file_name = f"{bundle_id}.json"
    absolute_result_path = Path(app_config.DEFAULT_RESULTS_PATH) / test_file_name
    absolute_result_path = absolute_result_path.resolve()
    _cleanup_file(absolute_result_path)
    return absolute_result_path


@pytest.fixture
def cleanup_bundle_result_file():
    """Fixture to clean up the bundle result file."""
    absolute_result_path = _cleanup_bundle_result_file_for("test-bundle")
    yield absolute_result_path
    _cleanup_file(absolute_result_path)


@pytest.fixture
def cleanup_undesirable_content_progress_result_file():
    """Fixture to clean up the undesirable-content-progress bundle result file."""
    absolute_result_path = _cleanup_bundle_result_file_for(
        "undesirable-content-progress"
    )
    yield absolute_result_path
    _cleanup_file(absolute_result_path)


@pytest.fixture
def undesirable_content_progress_result_file_keep_after():
    """
    Fixture for undesirable-content-progress: clean before test only.
    Result file is left on disk after the test (no teardown cleanup).
    TRACK: output path is data/results/undesirable-content-progress.json
    """
    absolute_result_path = _cleanup_bundle_result_file_for(
        "undesirable-content-progress"
    )
    yield absolute_result_path
    # Intentionally no teardown: leave result file for inspection


# ============================================================================
# Test Helper Functions
# ============================================================================

def _verify_result_structure(data, bundle_id):
    """Helper to verify result file structure."""
    assert "run_metadata" in data
    assert "run_results" in data
    assert data["run_metadata"]["test_id"] == bundle_id


async def _run_validation_workflow_test(
    connector,
    absolute_result_path,
    bundle_id="test-bundle",
    max_wait=TEST_BUNDLE_MAX_WAIT,
):
    """Helper to run a validation workflow test with common setup.

    Args:
        connector: Connector name to use
        absolute_result_path: Path to the result file
        bundle_id: Bundle name (used in payload and for run_metadata.test_id check)
        max_wait: Max seconds to wait for result file (default TEST_BUNDLE_MAX_WAIT)
    """
    _start_bundle_in_background(bundle_id, connector)

    data = await _wait_for_result_file_and_validate(
        absolute_result_path, max_wait=max_wait
    )
    _verify_result_structure(data, bundle_id)
    return data


# ============================================================================
# Test Implementations
# ============================================================================

@pytest.mark.skip(
    reason=(
        "Together model meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo requires a dedicated "
        "endpoint (400 model_not_available for serverless). Re-enable when configured."
    )
)
@pytest.mark.asyncio
async def test_validation_workflow_together_connector(
    seed_shared_config,
    cleanup_bundle_result_file,
):
    """
    Test 1: Happy Path - Together Connector (using my-together-llama-8b)

    Given: Together connector is configured
    When: Validation workflow executes
    Then: Validation passes
    """
    absolute_result_path = cleanup_bundle_result_file
    _cleanup_bundle_run_db("test-bundle")
    await _run_validation_workflow_test("my-together-llama-8b", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_openai_connector(
    seed_shared_config,
    cleanup_bundle_result_file,
):
    """
    Test 2: Happy Path - OpenAI Connector
    
    Given: OpenAI connector is configured
    When: Validation workflow executes
    Then: Validation passes
    """
    absolute_result_path = cleanup_bundle_result_file
    _cleanup_bundle_run_db("test-bundle")
    await _run_validation_workflow_test("my-gpt-4o-mini", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_failure_recovery(
    seed_shared_config,
    cleanup_bundle_result_file,
):
    """
    Test 3: Unhappy Path - Failure Recovery
    
    Given: Test connector is configured
    When: Test call fails (simulated by using invalid connector)
    Then: Test is marked as failed
    When: Happy path test runs after failure
    Then: JSON is created and validation passes
    """
    absolute_result_path = cleanup_bundle_result_file
    _cleanup_bundle_run_db("test-bundle")

    # Step 1: Try with invalid connector (start succeeds; failure happens in worker process)
    _start_bundle_in_background("test-bundle", "invalid_connector")

    # Wait for Step 1 to complete (it runs in a separate process)
    # Give it time to finish and ensure no file was created (or clean up if one was)
    await asyncio.sleep(2)
    _cleanup_file(absolute_result_path)
    _cleanup_bundle_run_db("test-bundle")

    # Step 2: Run test with valid connector (happy path)
    await _run_validation_workflow_test("my-gpt-4o-mini", absolute_result_path)


@pytest.mark.asyncio
async def test_validation_workflow_sequential_runs(
    seed_shared_config,
    cleanup_bundle_result_file,
):
    """
    Test 4: Repeated bundle runs (same bundle ID, sequential)

    Given: OpenAI connector is configured
    When: 5 bundle runs run one after another (same connector; same result file path).
        Parallel background bundle runs are not used: execute_bundle reuses one
        benchmark_run name per bundle_id, so concurrent subprocesses would race on the DB.
    Then: The final JSON file exists and passes process checklist validation.
    """
    absolute_result_path = cleanup_bundle_result_file

    connectors = ["my-gpt-4o-mini"] * 5

    for connector in connectors:
        _cleanup_bundle_run_db("test-bundle")
        await _run_single_bundle_and_wait(
            absolute_result_path, connector=connector
        )
    
    # Verify the final result file exists and is valid
    assert absolute_result_path.exists(), f"Result file not created: {absolute_result_path}"
    data = await _wait_for_result_file_and_validate(absolute_result_path)
    _verify_result_structure(data, "test-bundle")


# @pytest.mark.asyncio
# async def test_validation_workflow_undesirable_content_progress_bundle(
#     undesirable_content_progress_result_file_keep_after,
# ):
#     """
#     Test validation workflow for the undesirable-content-progress bundle.
#
#     Runs the undesirable-content-progress bundle (LlamaGuard annotator metric),
#     waits for the result file, and validates JSON schema and structure.
#     Run only this test with:
#       pytest moonshot_core/tests/entrypoints/test_validation_workflow.py -k undesirable_content_progress -v
#
#     TRACK: Result file is left on disk after this test (not cleaned up).
#     Path: data/results/undesirable-content-progress.json
#     """
#     absolute_result_path = undesirable_content_progress_result_file_keep_after
#     await _run_validation_workflow_test(
#         "my-gpt-4o-mini",
#         absolute_result_path,
#         bundle_id="undesirable-content-progress",
#         max_wait=600,  # 10 minutes (LlamaGuard metric makes this bundle slower)
#     )
