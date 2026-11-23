from unittest.mock import patch

import pytest

from adapters.feature_flag.env_feature_flag_adapter import EnvFeatureFlagAdapter
from domain.services.feature_flags import FeatureFlagNames


@pytest.fixture
def env_feature_flag_adapter():
    return EnvFeatureFlagAdapter()


def test_source_name(env_feature_flag_adapter):
    assert env_feature_flag_adapter.SOURCE_NAME == "env"


def test_load_flags_returns_valid_env_values(env_feature_flag_adapter, monkeypatch):
    name = FeatureFlagNames.AIVET_OCT2026_MOON771
    monkeypatch.setenv(str(name), "false")

    assert env_feature_flag_adapter.load_flags() == {str(name): False}


def test_load_flags_case_insensitive(env_feature_flag_adapter, monkeypatch):
    name = FeatureFlagNames.AIVET_OCT2026_MOON771
    monkeypatch.setenv(str(name), "TRUE")

    assert env_feature_flag_adapter.load_flags() == {str(name): True}


def test_load_flags_omits_unset_env_vars(env_feature_flag_adapter, monkeypatch):
    name = FeatureFlagNames.AIVET_OCT2026_MOON771
    monkeypatch.delenv(str(name), raising=False)

    assert str(name) not in env_feature_flag_adapter.load_flags()


@pytest.mark.parametrize("env_value", ["", "maybe", "1"])
def test_load_flags_omits_invalid_values_and_logs(
    env_feature_flag_adapter, monkeypatch, env_value
):
    name = FeatureFlagNames.AIVET_OCT2026_MOON771
    monkeypatch.setenv(str(name), env_value)

    with patch(
        "adapters.feature_flag.env_feature_flag_adapter.logger"
    ) as mock_logger:
        assert str(name) not in env_feature_flag_adapter.load_flags()
        mock_logger.error.assert_called_once()
