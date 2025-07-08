import pytest
from backend.map import get_map_color_mapping, load_map_data


def test_get_map_color_mapping():
    """Test that get_map_color_mapping returns the correct color mapping dictionary"""
    color_mapping = get_map_color_mapping()

    # Check that we get back a dictionary
    assert isinstance(color_mapping, dict)

    # Check the expected key-value pairs
    assert color_mapping["blue"] == "US NIST AI RMF"
    assert color_mapping["violet"] == "Hiroshima Process CoC"
    assert color_mapping["green"] == "ISO 42001"

    # Check that there are exactly 3 mappings
    assert len(color_mapping) == 3


def test_load_map_data(mocker):
    # Mock test data
    test_map_data = {
        "framework1": ["principle1", "principle2"],
        "framework2": ["principle3", "principle4"],
    }

    # Mock open() and json.load()
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    mocker.patch("json.load", return_value=test_map_data)

    # Test loading the data
    loaded_data = load_map_data()

    # Verify the loaded data matches test data
    assert loaded_data == test_map_data

    # Verify file was opened correctly
    mock_open.assert_called_once_with("assets/references/map.json", "r")


def test_load_map_data_file_error(mocker):
    # Mock open() to raise FileNotFoundError
    mocker.patch("builtins.open", side_effect=FileNotFoundError)

    # Test loading with file error
    with pytest.raises(FileNotFoundError):
        load_map_data()


def test_load_map_data_json_error(mocker):
    # Mock open() but make json.load() fail
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    mocker.patch("json.load", side_effect=ValueError("Invalid JSON"))

    # Test loading with JSON error
    with pytest.raises(ValueError):
        load_map_data()
