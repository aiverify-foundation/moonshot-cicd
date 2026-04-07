"""
Tests for the FastAPI application.
"""

import pytest
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.benchmark_run_test_bundle_entity import (
    BenchmarkRunTestBundleEntity,
)

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from entrypoints.api import app
from application.dto.model_config_dto import ModelConfigDTO, ProviderDatabaseConfigsDTO

client = TestClient(app)


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


@patch("entrypoints.api.BenchmarkRunService")
def test_list_benchmark_runs_empty(mock_service_class):
    """GET /api/benchmark-runs returns [] when no runs."""
    mock_svc = MagicMock()
    mock_service_class.return_value = mock_svc
    mock_svc.get_all_runs.return_value = []

    response = client.get("/api/benchmark-runs")
    assert response.status_code == 200
    assert response.json() == []


@patch("entrypoints.api.BenchmarkRunService")
def test_list_benchmark_runs_returns_runs(mock_service_class):
    """GET /api/benchmark-runs returns serialized benchmark runs."""
    t = datetime.now(timezone.utc)
    mock_svc = MagicMock()
    mock_service_class.return_value = mock_svc
    mock_svc.get_all_runs.return_value = [
        BenchmarkRunEntity(
            id=1,
            name="my-run",
            status="running",
            endpoint_type="LLM_Provider",
            start_time=t,
        ),
        BenchmarkRunEntity(
            id=2,
            name="done-run",
            status="completed",
            endpoint_type="LLM_Provider",
            start_time=t,
            end_time=t,
        ),
    ]

    response = client.get("/api/benchmark-runs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name"] == "my-run"
    assert data[0]["status"] == "running"
    assert data[1]["id"] == 2
    assert data[1]["status"] == "completed"
    mock_svc.get_all_runs.assert_called_once_with()


@patch("entrypoints.api.BenchmarkRunTestBundleQueryService")
def test_get_benchmark_run_test_bundles_empty(mock_service_class):
    """GET /api/benchmark-runs/{run_id}/run-test-bundles returns [] when none."""
    mock_svc = MagicMock()
    mock_service_class.return_value = mock_svc
    mock_svc.get_all_by_run_id.return_value = []

    response = client.get("/api/benchmark-runs/5/run-test-bundles")
    assert response.status_code == 200
    assert response.json() == []
    mock_svc.get_all_by_run_id.assert_called_once_with(5)


@patch("entrypoints.api.BenchmarkRunTestBundleQueryService")
def test_get_benchmark_run_test_bundles_returns_rows(mock_service_class):
    """GET /api/benchmark-runs/{run_id}/run-test-bundles returns serialized rows."""
    mock_svc = MagicMock()
    mock_service_class.return_value = mock_svc
    mock_svc.get_all_by_run_id.return_value = [
        BenchmarkRunTestBundleEntity(
            id=1, run_id=7, test_bundle_id=10, test_id=100
        ),
        BenchmarkRunTestBundleEntity(
            id=2, run_id=7, test_bundle_id=10, test_id=101
        ),
    ]

    response = client.get("/api/benchmark-runs/7/run-test-bundles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0] == {
        "id": 1,
        "run_id": 7,
        "test_bundle_id": 10,
        "test_id": 100,
    }
    assert data[1] == {
        "id": 2,
        "run_id": 7,
        "test_bundle_id": 10,
        "test_id": 101,
    }
    mock_svc.get_all_by_run_id.assert_called_once_with(7)


@patch("entrypoints.api.BenchmarkRunService")
def test_get_benchmark_run_not_found(mock_service_class):
    """GET /api/benchmark-runs/{run_id} returns 404 when missing."""
    mock_svc = MagicMock()
    mock_service_class.return_value = mock_svc
    mock_svc.get_run_by_id.return_value = None

    response = client.get("/api/benchmark-runs/999")
    assert response.status_code == 404
    mock_svc.get_run_by_id.assert_called_once_with(999)


@patch("entrypoints.api.BenchmarkRunService")
def test_get_benchmark_run_returns_run(mock_service_class):
    """GET /api/benchmark-runs/{run_id} returns one serialized run."""
    t = datetime.now(timezone.utc)
    mock_svc = MagicMock()
    mock_service_class.return_value = mock_svc
    mock_svc.get_run_by_id.return_value = BenchmarkRunEntity(
        id=3,
        name="single-run",
        status="completed",
        endpoint_type="LLM_Provider",
        start_time=t,
        end_time=t,
    )

    response = client.get("/api/benchmark-runs/3")
    assert response.status_code == 200
    assert response.json()["id"] == 3
    assert response.json()["name"] == "single-run"
    mock_svc.get_run_by_id.assert_called_once_with(3)


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


@patch('entrypoints.api.get_shared_config_seed_service')
def test_seed_shared_config_if_changed_seeded(mock_get_seed_service):
    """POST /api/seed-shared-config-if-changed returns seeded=True when service runs."""
    mock_service = MagicMock()
    mock_service.seed_if_test_file_changed.return_value = True
    mock_get_seed_service.return_value = mock_service

    response = client.post("/api/seed-shared-config-if-changed")
    assert response.status_code == 200
    data = response.json()
    assert data["seeded"] is True
    assert "updated" in data["message"].lower()
    mock_service.seed_if_test_file_changed.assert_called_once_with()


@patch('entrypoints.api.get_shared_config_seed_service')
def test_seed_shared_config_if_changed_skipped(mock_get_seed_service):
    """POST /api/seed-shared-config-if-changed returns seeded=False when file unchanged."""
    mock_service = MagicMock()
    mock_service.seed_if_test_file_changed.return_value = False
    mock_get_seed_service.return_value = mock_service

    response = client.post("/api/seed-shared-config-if-changed")
    assert response.status_code == 200
    data = response.json()
    assert data["seeded"] is False
    assert "skipped" in data["message"].lower() or "not changed" in data["message"].lower()
    mock_service.seed_if_test_file_changed.assert_called_once_with()


@patch('entrypoints.api.get_shared_config_seed_service')
def test_seed_shared_config_if_changed_404_when_file_not_found(mock_get_seed_service):
    """POST /api/seed-shared-config-if-changed returns 404 when config file not found."""
    mock_service = MagicMock()
    mock_service.seed_if_test_file_changed.side_effect = FileNotFoundError("Config not found")
    mock_get_seed_service.return_value = mock_service

    response = client.post("/api/seed-shared-config-if-changed")
    assert response.status_code == 404
    assert "detail" in response.json()


@patch('entrypoints.api.get_shared_config_seed_service')
def test_seed_shared_config_if_changed_400_on_validation_error(mock_get_seed_service):
    """POST /api/seed-shared-config-if-changed returns 400 on ValueError."""
    mock_service = MagicMock()
    mock_service.seed_if_test_file_changed.side_effect = ValueError("Missing dataset")
    mock_get_seed_service.return_value = mock_service

    response = client.post("/api/seed-shared-config-if-changed")
    assert response.status_code == 400
    assert "detail" in response.json()


@patch("entrypoints.api.provider_service")
def test_providers_with_database_model_configs(mock_provider_service):
    """GET /api/providers/with-database-model-configs returns service data as JSON."""
    t = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    mock_provider_service.list_providers_with_database_model_configs.return_value = [
        ProviderDatabaseConfigsDTO(
            providerName="OpenAI",
            configs=[
                ModelConfigDTO(
                    id="42",
                    name="default",
                    modelname="gpt-4",
                    providerID="openai",
                    savedConfigPairs={"temperature": "0.7"},
                    lastUpdated=t,
                )
            ],
        )
    ]
    response = client.get("/api/providers/with-database-model-configs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["providerName"] == "OpenAI"
    assert len(data[0]["configs"]) == 1
    cfg = data[0]["configs"][0]
    assert cfg["id"] == "42"
    assert cfg["name"] == "default"
    assert cfg["modelname"] == "gpt-4"
    assert cfg["providerID"] == "openai"
    assert cfg["savedConfigPairs"] == {"temperature": "0.7"}
    assert "lastUpdated" in cfg
    mock_provider_service.list_providers_with_database_model_configs.assert_called_once_with()
