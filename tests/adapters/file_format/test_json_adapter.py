import pytest
from unittest.mock import patch
from adapters.file_format.json_adapter import JsonAdapter


@pytest.fixture
def json_adapter():
    """
    Create a JsonAdapter instance for testing.
    
    Returns:
        JsonAdapter: A test JsonAdapter instance.
    """
    return JsonAdapter()


@pytest.mark.parametrize("data, expected_json, should_fail", [
    ({"key": "value"}, '{\n  "key": "value"\n}', False),
    ({"number": 123}, '{\n  "number": 123\n}', False),
    ({"key": {"set"}}, None, True),
])
def test_serialize(json_adapter, data, expected_json, should_fail):
    """
    Test the serialize method of JsonAdapter.
    
    Args:
        json_adapter: JsonAdapter instance fixture.
        data: Data to serialize.
        expected_json: Expected JSON string output.
        should_fail: Whether the serialization should fail.
    """
    with patch('adapters.file_format.json_adapter.logger') as mock_logger:
        result = json_adapter.serialize(data)
        if should_fail:
            assert result is None
            mock_logger.error.assert_called_once()
        else:
            assert result == expected_json


@pytest.mark.parametrize("json_content, expected_data, should_fail", [
    ('{"key": "value"}', {"key": "value"}, False),
    ('{"number": 123}', {"number": 123}, False),
    ('{"key": "value"', None, True),  # Missing closing brace
    ('{"number": 123', None, True),   # Missing closing brace
])
def test_deserialize(json_adapter, json_content, expected_data, should_fail):
    """
    Test the deserialize method of JsonAdapter.
    
    Args:
        json_adapter: JsonAdapter instance fixture.
        json_content: JSON string content to deserialize.
        expected_data: Expected deserialized data.
        should_fail: Whether the deserialization should fail.
    """
    with patch('adapters.file_format.json_adapter.logger') as mock_logger:
        result = json_adapter.deserialize(json_content)
        if should_fail:
            assert result is None
            mock_logger.error.assert_called_once()
        else:
            assert result == expected_data


@pytest.mark.parametrize("file_path, expected_support", [
    ("file.json", True),
    ("file.txt", False),
])
def test_supports(json_adapter, file_path, expected_support):
    """
    Test the supports method of JsonAdapter.
    
    Args:
        json_adapter: JsonAdapter instance fixture.
        file_path: File path to check support for.
        expected_support: Expected support result.
    """
    assert json_adapter.supports(file_path) == expected_support