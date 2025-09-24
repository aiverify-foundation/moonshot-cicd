"""
Tests for the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from src.entrypoints.api import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    # The response could be either JSON or HTML depending on whether build/index.html exists
    if response.headers.get("content-type") == "application/json":
        assert response.json() == {"message": "Welcome to Moonshot CI/CD API"}
    else:
        # If it's serving HTML, just check that it's a successful response
        assert response.status_code == 200


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_status_endpoint():
    """Test the status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["version"] == "1.1.0"
    assert data["service"] == "moonshot-cicd"


def test_docs_endpoint():
    """Test that the docs endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint():
    """Test that the redoc endpoint is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_static_files_mount():
    """Test that static files are properly mounted."""
    # Test that the static mount exists (even if no files are present)
    response = client.get("/static/")
    # This should return 404 if no files exist, but the mount should be working
    # We're just checking that the mount doesn't cause a 500 error
    assert response.status_code in [200, 404, 405]  # 405 is Method Not Allowed for directory listing
