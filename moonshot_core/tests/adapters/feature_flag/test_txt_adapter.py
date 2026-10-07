from unittest.mock import MagicMock, patch

import pytest

from adapters.feature_flag.txt_adapter import TxtAdapter
from domain.services.app_config import AppConfig


@pytest.fixture
def txt_adapter():
    """
    Create a TxtAdapter instance for testing.

    Returns:
        TxtAdapter: A test TxtAdapter instance.
    """
    return TxtAdapter()


def test_source_name(txt_adapter):
    assert txt_adapter.SOURCE_NAME == "file"


@pytest.mark.parametrize(
    "data, expected_txt, should_fail",
    [
        ({"B_FLAG": True, "A_FLAG": False}, "A_FLAG=false\nB_FLAG=true\n", False),
        ({}, "", False),
        (["not", "a", "dict"], None, True),
        ({"FLAG": "yes"}, None, True),
    ],
)
def test_format_flags(txt_adapter, data, expected_txt, should_fail):
    """
    Test the format_flags helper of TxtAdapter.
    """
    with patch("adapters.feature_flag.txt_adapter.logger") as mock_logger:
        result = txt_adapter.format_flags(data)
        if should_fail:
            assert result is None
            mock_logger.error.assert_called_once()
        else:
            assert result == expected_txt


@pytest.mark.parametrize(
    "txt_content, expected_data, invalid_line_count",
    [
        ("AIVET_Q42026_MOON774=true\n", {"AIVET_Q42026_MOON774": True}, 0),
        ("FLAG=FALSE\n", {"FLAG": False}, 0),
        ("# comment\nFLAG=true\n\n", {"FLAG": True}, 0),
        ("FLAG=true\nnot-a-flag\n=true\nFLAG2=maybe\n", {"FLAG": True}, 3),
        ("", {}, 0),
    ],
)
def test_parse_flags(txt_adapter, txt_content, expected_data, invalid_line_count):
    """
    Test the _parse_flags helper of TxtAdapter.
    """
    with patch("adapters.feature_flag.txt_adapter.logger") as mock_logger:
        result = txt_adapter._parse_flags(txt_content)
        assert result == expected_data
        assert mock_logger.error.call_count == invalid_line_count


def test_parse_flags_non_string_content(txt_adapter):
    """Non-string content should fail parsing."""
    with patch("adapters.feature_flag.txt_adapter.logger") as mock_logger:
        result = txt_adapter._parse_flags(None)
        assert result is None
        mock_logger.error.assert_called_once()


def test_load_flags_from_file(txt_adapter):
    storage = MagicMock()
    storage.read_file.return_value = "AIVET_Q42026_MOON774=true\nOTHER=false\n"

    with patch(
        "adapters.feature_flag.txt_adapter.StorageProviderFactory.get_adapter",
        return_value=storage,
    ) as mock_storage:
        result = txt_adapter.load_flags()
        assert result == {"AIVET_Q42026_MOON774": True, "OTHER": False}
        mock_storage.assert_called_once_with(AppConfig.DEFAULT_FEATURE_FLAGS_PATH)
        storage.read_file.assert_called_once_with(AppConfig.DEFAULT_FEATURE_FLAGS_PATH)


def test_load_flags_missing_file_returns_empty(txt_adapter):
    storage = MagicMock()
    storage.read_file.return_value = None

    with patch(
        "adapters.feature_flag.txt_adapter.StorageProviderFactory.get_adapter",
        return_value=storage,
    ):
        assert txt_adapter.load_flags() == {}


def test_load_flags_uses_env_path(txt_adapter, monkeypatch):
    monkeypatch.setenv(AppConfig.FEATURE_FLAGS_PATH_ENV_VAR, "/tmp/custom_flags.txt")
    storage = MagicMock()
    storage.read_file.return_value = "FLAG=true\n"

    with patch(
        "adapters.feature_flag.txt_adapter.StorageProviderFactory.get_adapter",
        return_value=storage,
    ) as mock_storage:
        assert txt_adapter.load_flags() == {"FLAG": True}
        mock_storage.assert_called_once_with("/tmp/custom_flags.txt")


def test_load_flags_exception_returns_empty(txt_adapter):
    with (
        patch(
            "adapters.feature_flag.txt_adapter.StorageProviderFactory.get_adapter",
            side_effect=RuntimeError("boom"),
        ),
        patch("adapters.feature_flag.txt_adapter.logger") as mock_logger,
    ):
        assert txt_adapter.load_flags() == {}
        mock_logger.error.assert_called_once()


def test_is_enabled_uses_load_flags(txt_adapter):
    with patch.object(
        txt_adapter, "load_flags", return_value={"AIVET_Q42026_MOON774": True}
    ):
        assert txt_adapter.is_enabled("AIVET_Q42026_MOON774") is True
        assert txt_adapter.is_enabled("MISSING") is False
