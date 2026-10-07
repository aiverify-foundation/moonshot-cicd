from unittest.mock import MagicMock, patch

import pytest

from adapters.feature_flag.txt_adapter import TxtAdapter
from domain.services.app_config import AppConfig
from domain.services.feature_flags import AIVET_Q42026_MOON774, FeatureFlags
from domain.services.loader.factory.feature_flag_adapter_factory import (
    FeatureFlagAdapterFactory,
)


@pytest.fixture(autouse=True)
def reset_feature_flags():
    FeatureFlags.reset()
    yield
    FeatureFlags.reset()


def test_is_enabled_true_from_loaded_flags():
    adapter = MagicMock()
    adapter.load_flags.return_value = {AIVET_Q42026_MOON774: True}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ) as mock_get:
        assert FeatureFlags().is_enabled(AIVET_Q42026_MOON774) is True
        mock_get.assert_called_once_with()
        adapter.load_flags.assert_called_once_with()


def test_is_enabled_false_for_missing_key():
    adapter = MagicMock()
    adapter.load_flags.return_value = {"OTHER": True}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ):
        assert FeatureFlags().is_enabled(AIVET_Q42026_MOON774) is False


def test_is_enabled_false_when_load_returns_empty():
    adapter = MagicMock()
    adapter.load_flags.return_value = {}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ):
        assert FeatureFlags().is_enabled(AIVET_Q42026_MOON774) is False


def test_is_enabled_false_when_load_returns_non_dict():
    adapter = MagicMock()
    adapter.load_flags.return_value = None

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ):
        assert FeatureFlags().is_enabled(AIVET_Q42026_MOON774) is False


def test_flags_are_cached_after_first_load():
    adapter = MagicMock()
    adapter.load_flags.return_value = {AIVET_Q42026_MOON774: True}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ) as mock_get:
        flags = FeatureFlags()
        assert flags.is_enabled(AIVET_Q42026_MOON774) is True
        assert flags.is_enabled(AIVET_Q42026_MOON774) is True
        mock_get.assert_called_once()
        adapter.load_flags.assert_called_once()


def test_load_exception_is_treated_as_disabled():
    with (
        patch(
            "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
            side_effect=RuntimeError("boom"),
        ),
        patch("domain.services.feature_flags.logger") as mock_logger,
    ):
        assert FeatureFlags().is_enabled(AIVET_Q42026_MOON774) is False
        mock_logger.error.assert_called_once()


def test_factory_returns_txt_adapter_for_default_source():
    adapter = FeatureFlagAdapterFactory.get_adapter()
    assert isinstance(adapter, TxtAdapter)
    assert adapter.SOURCE_NAME == AppConfig.DEFAULT_FEATURE_FLAGS_SOURCE


def test_factory_returns_txt_adapter_for_file_source(monkeypatch):
    monkeypatch.setenv(AppConfig.FEATURE_FLAGS_SOURCE_ENV_VAR, "file")
    adapter = FeatureFlagAdapterFactory.get_adapter()
    assert isinstance(adapter, TxtAdapter)
    assert adapter.SOURCE_NAME == "file"


def test_factory_raises_for_unknown_source(monkeypatch):
    monkeypatch.setenv(AppConfig.FEATURE_FLAGS_SOURCE_ENV_VAR, "dynamodb")
    with pytest.raises(RuntimeError, match="dynamodb"):
        FeatureFlagAdapterFactory.get_adapter()
