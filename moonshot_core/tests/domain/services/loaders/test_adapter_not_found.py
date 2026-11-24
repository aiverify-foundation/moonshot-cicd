"""Missing metric/connector adapter files raise AdapterNotFoundError with a clear message."""

from unittest.mock import MagicMock, patch

import pytest

from domain.services.benchmark_extensions import (
    AdapterNotFoundError,
    ensure_adapter_available,
    reset_invalid_extensions,
)
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.enums.module_types import ModuleTypes
from domain.services.feature_flags import FeatureFlags
from domain.services.loader.factory.storage_provider_factory import (
    StorageProviderFactory,
)
from domain.services.loader.module_loader import ModuleLoader

MISSING_METRIC = "no_such_metric_adapter_for_tests"
MISSING_CONNECTOR = "no_such_connector_adapter_for_tests"


def _patch_moon807(enabled: bool):
    adapter = MagicMock()
    adapter.load_flags.return_value = {
        FeatureFlagNames.AIVET_OCT2026_MOON807: enabled,
    }
    return patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    )


@pytest.fixture(autouse=True)
def fallback_storage(monkeypatch):
    """
    Use the real storage factory, so adapter names resolve to the discovered
    LocalStorageAdapter fallback. Do not replace the fallback class here: the factory
    discovers its own copy of the class, so an imported copy would not match.
    """
    assert StorageProviderFactory._fallback_adapter is not None
    monkeypatch.delenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", raising=False)
    reset_invalid_extensions()
    yield
    reset_invalid_extensions()


@pytest.fixture
def flag_off():
    with _patch_moon807(False):
        FeatureFlags._flags = None
        yield
    FeatureFlags._flags = None


@pytest.fixture
def flag_on():
    with _patch_moon807(True):
        FeatureFlags._flags = None
        yield
    FeatureFlags._flags = None


def test_missing_metric_adapter_raises_adapter_not_found(flag_off):
    with pytest.raises(AdapterNotFoundError) as excinfo:
        ModuleLoader.load(MISSING_METRIC, ModuleTypes.METRIC)

    assert isinstance(excinfo.value, FileNotFoundError)
    message = str(excinfo.value)
    assert f"metric adapter {MISSING_METRIC!r} not found" in message
    assert f"adapters/metric/{MISSING_METRIC}.py" in message
    assert "not in use" in message
    assert excinfo.value.module_type == ModuleTypes.METRIC
    assert excinfo.value.adapter_name == MISSING_METRIC


def test_missing_connector_adapter_raises_adapter_not_found(flag_off):
    with pytest.raises(AdapterNotFoundError) as excinfo:
        ModuleLoader.load(MISSING_CONNECTOR, ModuleTypes.CONNECTOR)

    assert f"connector adapter {MISSING_CONNECTOR!r} not found" in str(excinfo.value)
    assert excinfo.value.module_type == ModuleTypes.CONNECTOR
    assert excinfo.value.adapter_name == MISSING_CONNECTOR


def test_missing_adapter_message_names_extensions_dir_when_in_use(
    tmp_path, monkeypatch, flag_on
):
    ext_root = tmp_path / "extensions"
    (ext_root / "adapters" / "metric").mkdir(parents=True)
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    with pytest.raises(AdapterNotFoundError) as excinfo:
        ModuleLoader.load(MISSING_METRIC, ModuleTypes.METRIC)

    message = str(excinfo.value)
    expected_ext_path = ext_root.resolve() / "adapters" / "metric" / f"{MISSING_METRIC}.py"
    assert str(expected_ext_path) in message
    assert "was also checked" in message
    assert "not in use" not in message


def test_existing_adapter_file_error_is_not_masked(tmp_path, monkeypatch, flag_on):
    """A FileNotFoundError raised inside an adapter that exists is left as it is."""
    ext_root = tmp_path / "extensions"
    metric_dir = ext_root / "adapters" / "metric"
    metric_dir.mkdir(parents=True)
    (metric_dir / "broken_metric_for_tests.py").write_text(
        "raise FileNotFoundError('data file missing inside adapter')\n"
    )
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    with pytest.raises(FileNotFoundError) as excinfo:
        ModuleLoader.load("broken_metric_for_tests", ModuleTypes.METRIC)

    assert not isinstance(excinfo.value, AdapterNotFoundError)
    assert "data file missing inside adapter" in str(excinfo.value)


def test_ensure_adapter_available_returns_builtin_path(flag_on):
    path = ensure_adapter_available(ModuleTypes.METRIC, "refusal_adapter")

    assert path.endswith("refusal_adapter.py")


def test_ensure_adapter_available_raises_for_missing_metric(flag_off):
    with pytest.raises(AdapterNotFoundError, match="metric adapter"):
        ensure_adapter_available(ModuleTypes.METRIC, MISSING_METRIC)


def test_ensure_adapter_available_raises_for_missing_connector(flag_off):
    with pytest.raises(AdapterNotFoundError, match="connector adapter"):
        ensure_adapter_available(ModuleTypes.CONNECTOR, MISSING_CONNECTOR)
