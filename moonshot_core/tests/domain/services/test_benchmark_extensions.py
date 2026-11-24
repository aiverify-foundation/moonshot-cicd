"""Unit tests for benchmark extension merge and path helpers."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from adapters.storage_provider.local_storage_adapter import LocalStorageAdapter
from domain.entities.app_config_entity import AppConfigEntity
from domain.services.benchmark_extensions import (
    BenchmarkExtensionError,
    apply_app_config_extensions,
    compute_shared_config_fingerprint,
    find_adapter_collisions,
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
from domain.services.loader.factory.storage_provider_factory import (
    StorageProviderFactory,
)
from domain.services.loader.loader_types.metric_loader import MetricLoader


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


def _write_adapter(ext_root: Path, type_dirname: str, name: str) -> Path:
    adapter_dir = ext_root / "adapters" / type_dirname
    adapter_dir.mkdir(parents=True, exist_ok=True)
    path = adapter_dir / f"{name}.py"
    path.write_text("# stub\n")
    return path


def _collision_records(caplog):
    return [
        r
        for r in caplog.records
        if r.levelname == "ERROR" and "same name as built-in adapter" in r.getMessage()
    ]


def test_builtin_metric_adapter_wins_over_extension_with_same_name(
    tmp_path, monkeypatch, caplog
):
    ext_root = tmp_path / "extensions"
    _write_adapter(ext_root, "metric", "accuracy_adapter")
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    with caplog.at_level("ERROR"):
        path = resolve_adapter_module_path(ModuleTypes.METRIC, "accuracy_adapter")

    assert path == os.path.join("src/adapters", "metric", "accuracy_adapter.py")
    records = _collision_records(caplog)
    assert len(records) == 1
    assert "accuracy_adapter.py" in records[0].getMessage()


def test_builtin_connector_adapter_wins_over_extension_with_same_name(
    tmp_path, monkeypatch, caplog
):
    ext_root = tmp_path / "extensions"
    _write_adapter(ext_root, "connector", "openai_adapter")
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    with caplog.at_level("ERROR"):
        path = resolve_adapter_module_path(ModuleTypes.CONNECTOR, "openai_adapter")

    assert path == os.path.join("src/adapters", "connector", "openai_adapter.py")
    assert len(_collision_records(caplog)) == 1


def test_adapter_collision_is_logged_once_per_adapter(tmp_path, monkeypatch, caplog):
    ext_root = tmp_path / "extensions"
    _write_adapter(ext_root, "metric", "accuracy_adapter")
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    with caplog.at_level("ERROR"):
        for _ in range(3):
            resolve_adapter_module_path(ModuleTypes.METRIC, "accuracy_adapter")

    assert len(_collision_records(caplog)) == 1


def test_non_colliding_extension_adapter_is_used_and_not_reported(
    tmp_path, monkeypatch, caplog
):
    ext_root = tmp_path / "extensions"
    custom = _write_adapter(ext_root, "metric", "only_in_extension_adapter")
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    with caplog.at_level("ERROR"):
        path = resolve_adapter_module_path(
            ModuleTypes.METRIC, "only_in_extension_adapter"
        )

    assert path == str(custom)
    assert _collision_records(caplog) == []


def test_find_adapter_collisions_lists_only_shadowed_files(tmp_path):
    ext_root = tmp_path / "extensions"
    shadowed_metric = _write_adapter(ext_root, "metric", "accuracy_adapter")
    shadowed_connector = _write_adapter(ext_root, "connector", "openai_adapter")
    _write_adapter(ext_root, "metric", "only_in_extension_adapter")

    assert find_adapter_collisions(ext_root) == sorted(
        [shadowed_connector, shadowed_metric]
    )


def test_find_adapter_collisions_empty_without_adapters_dir(tmp_path):
    assert find_adapter_collisions(tmp_path) == []


def test_metric_loader_uses_builtin_path_on_adapter_name_collision(
    tmp_path, monkeypatch
):
    ext_root = tmp_path / "extensions"
    _write_adapter(ext_root, "metric", "accuracy_adapter")
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    # The fallback adapter is only registered after storage-provider discovery.
    monkeypatch.setattr(
        StorageProviderFactory, "_fallback_adapter", LocalStorageAdapter
    )
    with patch.object(
        LocalStorageAdapter,
        "load_module",
        return_value=("instance", "accuracy_adapter"),
    ) as load_module:
        MetricLoader(LocalStorageAdapter()).load("accuracy_adapter")

    assert load_module.call_args[0][2] == os.path.join(
        "src/adapters", "metric", "accuracy_adapter.py"
    )


def test_startup_reports_adapter_collision_and_keeps_overlay(
    tmp_path, monkeypatch, caplog
):
    ext_root = tmp_path / "extensions"
    _write_adapter(ext_root, "metric", "accuracy_adapter")
    (ext_root / "moonshot_config.yaml").write_text(
        yaml.safe_dump(
            {
                "connectors_configurations": [
                    {"id": "ext-conn", "connector_adapter": "x"}
                ]
            }
        )
    )
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(ext_root))

    with caplog.at_level("ERROR"):
        merged = apply_app_config_extensions(AppConfigEntity())

    assert len(_collision_records(caplog)) == 1
    assert [c["id"] for c in merged.connectors_configurations] == ["ext-conn"]
    assert resolve_extensions_dir() == ext_root.resolve()


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


def test_resolve_extensions_dir_uses_docker_volume_when_env_unset(
    tmp_path, monkeypatch
):
    import domain.services.benchmark_extensions as be

    data_dir = tmp_path / "moonshot"
    volume_ext = data_dir / "benchmark-extensions"
    volume_ext.mkdir(parents=True)
    monkeypatch.setattr(be, "DOCKER_DATA_DIR", data_dir)
    monkeypatch.delenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", raising=False)

    assert resolve_extensions_dir() == volume_ext.resolve()


def test_resolve_extensions_dir_none_when_volume_missing_even_if_app_root_has_folder(
    tmp_path, monkeypatch
):
    import domain.services.benchmark_extensions as be

    data_dir = tmp_path / "moonshot"
    data_dir.mkdir()
    app_root = tmp_path / "app"
    (app_root / "benchmark-extensions").mkdir(parents=True)
    monkeypatch.setattr(be, "DOCKER_DATA_DIR", data_dir)
    monkeypatch.setattr(be, "get_application_root", lambda: app_root)
    monkeypatch.delenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", raising=False)

    assert resolve_extensions_dir() is None


def test_resolve_extensions_dir_env_wins_over_docker_volume(tmp_path, monkeypatch):
    import domain.services.benchmark_extensions as be

    data_dir = tmp_path / "moonshot"
    (data_dir / "benchmark-extensions").mkdir(parents=True)
    env_ext = tmp_path / "env-extensions"
    env_ext.mkdir()
    monkeypatch.setattr(be, "DOCKER_DATA_DIR", data_dir)
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(env_ext))

    assert resolve_extensions_dir() == env_ext.resolve()


def test_resolve_extensions_dir_none_when_env_is_not_a_directory(tmp_path, monkeypatch):
    import domain.services.benchmark_extensions as be

    data_dir = tmp_path / "moonshot"
    (data_dir / "benchmark-extensions").mkdir(parents=True)
    monkeypatch.setattr(be, "DOCKER_DATA_DIR", data_dir)
    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(tmp_path / "missing"))

    assert resolve_extensions_dir() is None
