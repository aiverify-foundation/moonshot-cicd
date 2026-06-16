"""
Integration tests: exported GA Schema1 JSON validates and includes every run prompt.

Maps to ga_schema1_json_acceptance_criteria.txt lines 132-160.
Uses fixture data from system_test/fixtures/e2e_run_ac1.json (moonshot.db run id 3).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

MOONSHOT_CORE_ROOT = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = MOONSHOT_CORE_ROOT.parent
_SRC = MOONSHOT_CORE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.driven.repository.sqlalchemy.session_manager import SessionManager  # noqa: E402
from entrypoints.api import app  # noqa: E402
from process_check_app.backend.report_validation import validate_json  # noqa: E402
from process_check_app.backend.schema.ms_ga_schema import Schema1  # noqa: E402
from system_test.scripts.seed_completed_download_run import (  # noqa: E402
    DEFAULT_FIXTURE_PATH,
    seed_completed_download_run,
)

EXPECTED_RUN_NAME = "AC1"
EXPECTED_PROMPT_COUNT = 24


@pytest.fixture(scope="function")
def test_db_path():
    db_path = (
        MOONSHOT_CORE_ROOT
        / "data"
        / "database"
        / "moonshot_pytest_export_schema1.db"
    )
    if db_path.exists():
        db_path.unlink()
    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch, tmp_path):
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield tmp_path
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


def collect_export_prompt_ids_by_test_name(data: dict) -> dict[str, set[int]]:
    """Map test_name -> prompt_ids from exported GA Schema1 JSON."""
    by_test: dict[str, set[int]] = {}
    for entry in data.get("run_results", []):
        test_name = entry.get("metadata", {}).get("test_name", "")
        prompt_ids: set[int] = set()
        individual = entry.get("results", {}).get("individual_results", {})
        for bucket in individual.values():
            for prompt in bucket:
                prompt_ids.add(int(prompt["prompt_id"]))
        by_test[test_name] = prompt_ids
    return by_test


def collect_results_prompt_ids_by_test_name(results: dict) -> dict[str, set[int]]:
    """Map test_name -> prompt_ids from GET .../results (Test Results source of truth)."""
    by_test: dict[str, set[int]] = {}
    for prompt in results.get("prompts", []):
        test_name = prompt.get("test_name") or ""
        by_test.setdefault(test_name, set()).add(int(prompt["prompt_id"]))
    return by_test


def collect_all_export_prompt_ids(data: dict) -> list[int]:
    ids: list[int] = []
    for entry in data.get("run_results", []):
        individual = entry.get("results", {}).get("individual_results", {})
        for bucket in individual.values():
            for prompt in bucket:
                ids.append(int(prompt["prompt_id"]))
    return ids


@pytest.mark.integration
def test_exported_json_is_schema1_complete(test_db_env, tmp_path):
    """Downloaded export JSON validates as Schema1 and contains every results-page prompt."""
    manifest_path = tmp_path / "download-run-manifest.json"
    manifest = seed_completed_download_run(
        fixture_path=DEFAULT_FIXTURE_PATH,
        manifest_path=manifest_path,
    )
    run_id = manifest["runId"]
    assert manifest["runName"] == EXPECTED_RUN_NAME
    assert manifest["expectedPromptCount"] == EXPECTED_PROMPT_COUNT

    client = TestClient(app)
    results_response = client.get(f"/api/benchmark-runs/{run_id}/results")
    assert results_response.status_code == 200, results_response.text
    results_data = results_response.json()

    export_response = client.get(f"/api/benchmark-runs/{run_id}/export")
    assert export_response.status_code == 200, export_response.text
    assert export_response.headers["content-type"] == "application/json"
    assert export_response.headers["content-disposition"] == (
        f'attachment; filename="{EXPECTED_RUN_NAME}.json"'
    )

    export_data = json.loads(export_response.text)

    Schema1(**export_data)
    assert validate_json(export_data) is True

    assert "run_metadata" in export_data
    assert isinstance(export_data["run_results"], list)
    assert len(export_data["run_results"]) >= 1

    results_test_ids = {
        p["test_id"] for p in results_data["prompts"] if p.get("test_id") is not None
    }
    assert len(export_data["run_results"]) == len(results_test_ids)

    for entry in export_data["run_results"]:
        assert "metadata" in entry
        assert "results" in entry
        assert "individual_results" in entry["results"]
        assert len(entry["results"]["individual_results"]) >= 1
        assert "evaluation_summary" in entry["results"]
        assert len(entry["results"]["evaluation_summary"]) >= 1

    results_prompts = results_data["prompts"]
    assert len(results_prompts) == EXPECTED_PROMPT_COUNT

    exported_ids = collect_all_export_prompt_ids(export_data)
    assert len(exported_ids) == len(results_prompts)
    assert Counter(exported_ids) == Counter(
        int(p["prompt_id"]) for p in results_prompts
    )

    results_by_test = collect_results_prompt_ids_by_test_name(results_data)
    export_by_test = collect_export_prompt_ids_by_test_name(export_data)
    assert set(export_by_test) == set(results_by_test)
    for test_name, expected_ids in results_by_test.items():
        assert export_by_test.get(test_name) == expected_ids
