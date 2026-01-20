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
