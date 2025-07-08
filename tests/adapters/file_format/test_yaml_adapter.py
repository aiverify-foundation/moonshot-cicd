"""
Tests for the YamlAdapter class.

This module contains comprehensive tests for the YamlAdapter class, which handles
serialization and deserialization of YAML data, as well as file format support detection.
"""

import pytest
from unittest.mock import patch
from adapters.file_format.yaml_adapter import YamlAdapter

@pytest.fixture
def yaml_adapter():
    """Create a YamlAdapter instance for testing."""
    return YamlAdapter()

@pytest.mark.parametrize("data, expected_yaml, should_fail", [
    ({"key": "value"}, "key: value\n", False),
    ({"number": 123}, "number: 123\n", False),
    ({"key": {"set"}}, None, True),
])
def test_serialize(yaml_adapter, data, expected_yaml, should_fail):
    """
    Test the serialize method of YamlAdapter.
    
    Tests various data types and structures to ensure proper YAML serialization,
    including error handling for non-serializable data types like sets.
    """
    with patch('adapters.file_format.yaml_adapter.logger') as mock_logger:
        result = yaml_adapter.serialize(data)
        if should_fail:
            assert result is None
            mock_logger.error.assert_called_once()
        else:
            assert result == expected_yaml

@pytest.mark.parametrize("yaml_content, expected_data, should_fail", [
    ("key: value\n", {"key": "value"}, False),
    ("number: 123\n", {"number": 123}, False),
    ("key: value", {"key": "value"}, False),  # Valid YAML without newline
    ("key: value\nnumber: 123", {"key": "value", "number": 123}, False),
    ("key: value\nnumber: 123\n", {"key": "value", "number": 123}, False),
    ("key: value\nnumber: 123\ninvalid_yaml", None, True),  # Invalid YAML
])
def test_deserialize(yaml_adapter, yaml_content, expected_data, should_fail):
    """
    Test the deserialize method of YamlAdapter.
    
    Tests various YAML content formats including valid YAML with and without
    trailing newlines, multi-line YAML, and invalid YAML content to ensure
    proper error handling.
    """
    with patch('adapters.file_format.yaml_adapter.logger') as mock_logger:
        result = yaml_adapter.deserialize(yaml_content)
        if should_fail:
            assert result is None
            mock_logger.error.assert_called_once()
        else:
            assert result == expected_data

@pytest.mark.parametrize("file_path, expected_support", [
    ("file.yaml", True),
    ("file.txt", False),
])
def test_supports(yaml_adapter, file_path, expected_support):
    """
    Test the supports method of YamlAdapter.
    
    Verifies that the adapter correctly identifies supported file formats
    based on file extensions.
    """
    assert yaml_adapter.supports(file_path) == expected_support