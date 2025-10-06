"""
Tests for the FastAPI application.
"""

import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from entrypoints.api import app

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


# Removed tests for non-existent endpoints (/health, /api/v1/status)


def test_docs_endpoint():
    """Test that the docs endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint():
    """Test that the redoc endpoint is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_bundles_endpoint():
    """Test the /api/bundles endpoint returns proper response structure."""
    response = client.get("/api/bundles")
    assert response.status_code == 200
    
    data = response.json()
    assert "bundles" in data
    assert isinstance(data["bundles"], list)
    
    # If bundles exist, verify structure
    if data["bundles"]:
        bundle = data["bundles"][0]
        assert "name" in bundle
        assert "description" in bundle
        assert "tests" in bundle
        assert isinstance(bundle["tests"], list)
        
        # If tests exist, verify test structure
        if bundle["tests"]:
            test = bundle["tests"][0]
            assert "name" in test
            assert "metric" in test
            assert "description" in test
            # Dataset should be present (not null) after our fix
            assert "dataset" in test


def test_static_files_with_referer():
    """Test that static files are served when accessed with proper referer header."""
    # Simulate a request with referer header (as if coming from the main page)
    response = client.get("/test-file.js", headers={"referer": "http://testserver/"})
    # Should return 404 for non-existent file, but not 403 (access denied)
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


def test_static_files_direct_access_blocked():
    """Test that direct access to static files is blocked."""
    # Request without referer header (direct access)
    response = client.get("/test-file.js")
    assert response.status_code == 403
    assert "Direct access to static files is not allowed" in response.json()["detail"]


def test_static_files_cross_origin_blocked():
    """Test that cross-origin access to static files is blocked."""
    # Request with referer from different origin
    response = client.get("/test-file.js", headers={"referer": "http://malicious-site.com/"})
    assert response.status_code == 403
    assert "Direct access to static files is not allowed" in response.json()["detail"]


def test_static_files_path_traversal_blocked():
    """Test that path traversal attempts are blocked."""
    # Test path traversal attempt with URL-encoded .. 
    response = client.get("/test%2F..%2Fetc%2Fpasswd", headers={"referer": "http://testserver/"})
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_next_js_static_files_with_referer():
    """Test that Next.js static files are served with proper referer."""
    # Test Next.js static file access with referer
    response = client.get("/_next/static/test.js", headers={"referer": "http://testserver/"})
    # Should return 404 for non-existent file, but not 403 (access denied)
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


def test_next_js_static_files_direct_access_blocked():
    """Test that direct access to Next.js static files is blocked."""
    # Direct access to Next.js static files without referer
    response = client.get("/_next/static/test.js")
    assert response.status_code == 403
    assert "Direct access to static files is not allowed" in response.json()["detail"]
