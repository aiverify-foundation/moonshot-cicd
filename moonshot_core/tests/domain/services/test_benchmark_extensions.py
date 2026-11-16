"""Unit tests for benchmark extension merge and path helpers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from domain.entities.app_config_entity import AppConfigEntity
from domain.services.benchmark_extensions import (
    BenchmarkExtensionError,
    compute_shared_config_fingerprint,
    load_merged_shared_config,
    merge_app_config_entity,
    merge_shared_config,
    resolve_adapter_module_path,
    resolve_extensions_dir,
    validate_extension_dataset_ids,
)
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.enums.module_types import ModuleTypes
from domain.services.feature_flags import FeatureFlags


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
def moon807_enabled():
    """Benchmark extension path tests assume MOON807 is on."""
    with _patch_moon807(True):
        FeatureFlags._flags = None
        yield
        FeatureFlags._flags = None


def test_merge_shared_config_appends_bundle():
    base = {"builtin": {"name": "Built-in", "tests": []}}
    overlay = {"custom": {"name": "Custom", "tests": []}}
    merged = merge_shared_config(base, overlay)
    assert set(merged.keys()) == {"builtin", "custom"}


def test_merge_shared_config_rejects_duplicate_bundle_key():
    base = {"same-key": {"tests": []}}
    overlay = {"same-key": {"tests": []}}
    with pytest.raises(BenchmarkExtensionError, match="duplicates built-in bundle"):
        merge_shared_config(base, overlay)


def test_merge_app_config_appends_connector():
    base = AppConfigEntity(
        connectors_configurations=[{"id": "a", "connector_adapter": "openai_adapter"}]
    )
    overlay = {
        "connectors_configurations": [
            {"id": "b", "connector_adapter": "openai_adapter", "model": "gpt-4o"}
        ]
    }
    merged = merge_app_config_entity(base, overlay)
    assert [c["id"] for c in merged.connectors_configurations] == ["a", "b"]


def test_merge_app_config_rejects_duplicate_connector_id():
    base = AppConfigEntity(
        connectors_configurations=[{"id": "dup", "connector_adapter": "x"}]
    )
    overlay = {"connectors_configurations": [{"id": "dup", "connector_adapter": "y"}]}
    with pytest.raises(BenchmarkExtensionError, match="duplicates built-in"):
        merge_app_config_entity(base, overlay)


def test_validate_extension_dataset_ids_rejects_builtin_collision(tmp_path):
    builtin = tmp_path / "builtin"
    ext_root = tmp_path / "ext"
    builtin.mkdir()
    ext_datasets = ext_root / "datasets"
    ext_datasets.mkdir(parents=True)
    (builtin / "foo.json").write_text("{}")
    (ext_datasets / "foo.json").write_text("{}")
    with pytest.raises(BenchmarkExtensionError, match="duplicates built-in dataset"):
        validate_extension_dataset_ids(ext_root, builtin)


def test_fingerprint_changes_when_extension_shared_yaml_changes(tmp_path, monkeypatch):
    base = tmp_path / "shared.yaml"
    base.write_text("a: 1\n")
    ext_root = tmp_path / "extensions"
    ext_shared = ext_root / "test_configs"
    ext_shared.mkdir(parents=True)
    fp1 = compute_shared_config_fingerprint(base)
    (ext_shared / "shared.yaml").write_text("b: 2\n")
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))
    fp2 = compute_shared_config_fingerprint(base)
    assert fp1 != fp2


def test_resolve_adapter_module_path_prefers_extension(tmp_path, monkeypatch):
    ext_root = tmp_path / "extensions"
    metric_dir = ext_root / "adapters" / "metric"
    metric_dir.mkdir(parents=True)
    custom = metric_dir / "my_metric_adapter.py"
    custom.write_text("# stub\n")
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))
    path = resolve_adapter_module_path(ModuleTypes.METRIC, "my_metric_adapter")
    assert path == str(custom)


def test_load_merged_shared_config_from_files(tmp_path, monkeypatch):
    base = tmp_path / "shared.yaml"
    yaml.safe_dump({"base-bundle": {"tests": []}}, base.open("w"))
    ext_root = tmp_path / "extensions"
    ext_shared_dir = ext_root / "test_configs"
    ext_shared_dir.mkdir(parents=True)
    yaml.safe_dump(
        {"ext-bundle": {"tests": []}},
        (ext_shared_dir / "shared.yaml").open("w"),
    )
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))
    merged = load_merged_shared_config(base)
    assert set(merged.keys()) == {"base-bundle", "ext-bundle"}


def test_resolve_extensions_dir_none_when_moon807_disabled(tmp_path, monkeypatch):
    ext_root = tmp_path / "extensions"
    ext_root.mkdir()
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    FeatureFlags._flags = None
    with _patch_moon807(False):
        FeatureFlags._flags = None
        assert resolve_extensions_dir() is None


def test_load_merged_shared_config_base_only_when_moon807_disabled(
    tmp_path, monkeypatch
):
    base = tmp_path / "shared.yaml"
    yaml.safe_dump({"base-bundle": {"tests": []}}, base.open("w"))
    ext_root = tmp_path / "extensions"
    ext_shared_dir = ext_root / "test_configs"
    ext_shared_dir.mkdir(parents=True)
    yaml.safe_dump(
        {"ext-bundle": {"tests": []}},
        (ext_shared_dir / "shared.yaml").open("w"),
    )
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    FeatureFlags._flags = None
    with _patch_moon807(False):
        FeatureFlags._flags = None
        merged = load_merged_shared_config(base)
    assert merged == {"base-bundle": {"tests": []}}
