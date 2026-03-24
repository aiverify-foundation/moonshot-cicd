"""
Tests for the start-benchmark-run API (run multiple bundles under one run).

Uses the same bundle as test_validation_workflow (test-prompts) and the same
result file path and validation helpers. Exercises POST /api/start-benchmark-run
with a single bundle so we can wait for the result file and validate it.

Note: Uses a dedicated SQLite file (MOONSHOT_DB_PATH) so benchmark_run names do not
collide with the developer moonshot.db. Migrations run on first SessionManager init.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from domain.services.app_config import AppConfig
from entrypoints.api import app
from process_check_app.backend.report_validation import validate_json


# Bundle and connector used in test_validation_workflow
BUNDLE_NAME = "test-prompts"
CONNECTOR = "my-gpt-4o-mini"
LLM_PROVIDER_NAME = "OpenAI"


def _cleanup_file(file_path):
    """Remove a file if it exists."""
    if file_path.exists():
        file_path.unlink()
    if os.path.exists(str(file_path.resolve())):
        try:
            os.remove(str(file_path.resolve()))
        except OSError:
            pass


def _result_path_for_bundle(bundle_id: str) -> Path:
    """Absolute path to the result JSON file for a bundle."""
    app_config = AppConfig()
    return (Path(app_config.DEFAULT_RESULTS_PATH) / f"{bundle_id}.json").resolve()


async def _wait_for_result_file_and_validate(absolute_result_path, max_wait=15):
    """Wait for result file to appear and validate JSON schema."""
    wait_interval = 0.2
    waited = 0
    while waited < max_wait:
        if absolute_result_path.exists():
            break
        await asyncio.sleep(wait_interval)
        waited += wait_interval

    assert absolute_result_path.exists(), (
        f"Result file not created after {waited:.1f}s. Expected: {absolute_result_path}"
    )

    with open(absolute_result_path, "r") as f:
        data = json.load(f)

    is_valid = validate_json(data)
    assert is_valid, (
        "JSON output does not conform to expected schema (Schema1 or Schema2).\n"
        f"Data structure: {json.dumps(data, indent=2)[:1000]}..."
    )
    return data


@pytest.fixture
def cleanup_test_prompts_result_file():
    """Clean up the test-prompts bundle result file before and after test."""
    absolute_result_path = _result_path_for_bundle(BUNDLE_NAME)
    _cleanup_file(absolute_result_path)
    yield absolute_result_path
    _cleanup_file(absolute_result_path)


@pytest.mark.asyncio
async def test_run_benchmark_run_with_test_prompts_bundle(
    seed_shared_config,
    cleanup_test_prompts_result_file,
):
    """
    Run the start-benchmark-run API with the test-prompts bundle (same as
    test_validation_workflow), wait for the result file, and validate it.

    POST /api/start-benchmark-run with bundle_names=["test-prompts"] and
    connector (llm_provider_config_name) my-gpt-4o-mini. Asserts the run
    starts successfully and the result JSON is written and passes schema
    validation.
    """
    absolute_result_path = cleanup_test_prompts_result_file

    payload = {
        "run_name": "entrypoint-test-run",
        "bundle_names": [BUNDLE_NAME],
        "llm_provider_name": LLM_PROVIDER_NAME,
        "llm_provider_config_name": CONNECTOR,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/start-benchmark-run", json=payload)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "message" in data
    assert "started" in data["message"].lower() or "success" in data["message"].lower()

    # Wait for the bundle process to write the result file (same path as run-bundle)
    result_data = await _wait_for_result_file_and_validate(
        absolute_result_path, max_wait=15
    )

    assert "run_metadata" in result_data
    assert "run_results" in result_data
    assert result_data["run_metadata"]["test_id"] == BUNDLE_NAME
