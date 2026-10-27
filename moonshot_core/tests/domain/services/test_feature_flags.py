from unittest.mock import MagicMock, patch

import pytest

from adapters.feature_flag.txt_adapter import TxtAdapter
from domain.services.app_config import AppConfig
from domain.services.feature_flags import FeatureFlagNames, FeatureFlags
from domain.services.loader.factory.feature_flag_adapter_factory import (
    FeatureFlagAdapterFactory,
)


@pytest.fixture(autouse=True)
def reset_feature_flags():
    FeatureFlags.reset()
    yield
    FeatureFlags.reset()


@pytest.fixture(autouse=True)
def empty_env_overrides():
    with patch("domain.services.feature_flags.EnvFeatureFlagAdapter") as mock_env_cls:
        mock_env_cls.return_value.load_flags.return_value = {}
        yield mock_env_cls


def test_is_enabled_true_from_loaded_flags():
    adapter = MagicMock()
    adapter.load_flags.return_value = {FeatureFlagNames.AIVET_Q42026_MOON774: True}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ) as mock_get:
        assert (
            FeatureFlags().is_enabled(FeatureFlagNames.AIVET_Q42026_MOON774) is True
        )
        mock_get.assert_called_once_with()
        adapter.load_flags.assert_called_once_with()


def test_is_enabled_false_for_missing_key():
    adapter = MagicMock()
    adapter.load_flags.return_value = {"OTHER": True}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ):
        assert (
            FeatureFlags().is_enabled(FeatureFlagNames.AIVET_Q42026_MOON774) is False
        )


def test_is_enabled_false_when_load_returns_empty():
    adapter = MagicMock()
    adapter.load_flags.return_value = {}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ):
        assert (
            FeatureFlags().is_enabled(FeatureFlagNames.AIVET_Q42026_MOON774) is False
        )


def test_is_enabled_false_when_load_returns_non_dict():
    adapter = MagicMock()
    adapter.load_flags.return_value = None

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ):
        assert (
            FeatureFlags().is_enabled(FeatureFlagNames.AIVET_Q42026_MOON774) is False
        )


def test_flags_are_cached_after_first_load():
    adapter = MagicMock()
    adapter.load_flags.return_value = {FeatureFlagNames.AIVET_Q42026_MOON774: True}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ) as mock_get:
        flags = FeatureFlags()
        assert flags.is_enabled(FeatureFlagNames.AIVET_Q42026_MOON774) is True
        assert flags.is_enabled(FeatureFlagNames.AIVET_Q42026_MOON774) is True
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
        assert (
            FeatureFlags().is_enabled(FeatureFlagNames.AIVET_Q42026_MOON774) is False
        )
        mock_logger.error.assert_called_once()


def test_get_all_returns_loaded_flags():
    adapter = MagicMock()
    adapter.load_flags.return_value = {
        FeatureFlagNames.AIVET_Q42026_MOON774: True,
        "OTHER": False,
    }

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    ):
        assert FeatureFlags().get_all() == {
            str(FeatureFlagNames.AIVET_Q42026_MOON774): True,
            "OTHER": False,
        }


def test_get_all_returns_empty_on_load_failure():
    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        side_effect=RuntimeError("boom"),
    ):
        assert FeatureFlags().get_all() == {}


def test_env_override_false_over_file_true(empty_env_overrides):
    name = FeatureFlagNames.AIVET_OCT2026_MOON771
    base = MagicMock()
    base.load_flags.return_value = {name: True}
    empty_env_overrides.return_value.load_flags.return_value = {str(name): False}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=base,
    ):
        flags = FeatureFlags()
        assert flags.is_enabled(name) is False
        assert flags.get_all() == {str(name): False}


def test_env_override_ignored_for_flag_not_in_base(empty_env_overrides):
    name = FeatureFlagNames.AIVET_OCT2026_MOON771
    base = MagicMock()
    base.load_flags.return_value = {"OTHER": True}
    empty_env_overrides.return_value.load_flags.return_value = {str(name): True}

    with patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=base,
    ):
        assert FeatureFlags().get_all() == {"OTHER": True}


def test_apply_env_overrides_static():
    assert FeatureFlags._apply_env_overrides(
        {"A": True, "B": False},
        {"A": False, "C": True},
    ) == {"A": False, "B": False}


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
