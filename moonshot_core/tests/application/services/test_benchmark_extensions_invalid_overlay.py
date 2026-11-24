"""
An unusable benchmark-extensions overlay is dropped as a whole.

Every hook (config merge, seed merge, dataset search, adapter resolution) goes through
``resolve_extensions_dir()``, so once an overlay is marked invalid the built-in
benchmarks, datasets, adapters and config are used and the overlay is not half-applied.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from application.services.shared_config_seed_service import (
    SharedConfigSeedService,
)
from domain.entities.moonshot_config_entity import MoonshotConfigEntity
from domain.services import benchmark_extensions as be
from domain.services.app_config import AppConfig
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.enums.module_types import ModuleTypes
from domain.services.feature_flags import FeatureFlags

MOONSHOT_CORE_ROOT = Path(__file__).resolve().parents[3]


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
    be.reset_invalid_extensions()
    with _patch_moon807(True):
        FeatureFlags._flags = None
        yield
    FeatureFlags._flags = None
    be.reset_invalid_extensions()


@pytest.fixture(autouse=True)
def isolated_app_config(monkeypatch):
    """Fresh AppConfig built from the real config, restored afterwards."""
    monkeypatch.chdir(MOONSHOT_CORE_ROOT)
    saved = (AppConfig._instance, AppConfig._config)
    AppConfig._instance = None
    AppConfig._config = None
    yield
    AppConfig._instance, AppConfig._config = saved


def _write_overlay(
    root: Path,
    *,
    shared: dict | None = None,
    config: dict | str | None = None,
    datasets: tuple[str, ...] = (),
    metric_adapters: tuple[str, ...] = (),
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if shared is not None:
        (root / "test_configs").mkdir(exist_ok=True)
        (root / "test_configs" / "shared.yaml").write_text(yaml.safe_dump(shared))
    if config is not None:
        text = config if isinstance(config, str) else yaml.safe_dump(config)
        (root / "moonshot_config.yaml").write_text(text)
    if datasets:
        (root / "datasets").mkdir(exist_ok=True)
        for name in datasets:
            (root / "datasets" / f"{name}.json").write_text("{}")
    if metric_adapters:
        (root / "adapters" / "metric").mkdir(parents=True, exist_ok=True)
        for name in metric_adapters:
            (root / "adapters" / "metric" / f"{name}.py").write_text("# stub\n")
    return root


def _bundle(dataset: str, metric: str = "accuracy_adapter") -> dict:
    return {
        "name": "Ext",
        "tests": [{"name": "T", "dataset": dataset, "metric": {"name": metric}}],
    }


@pytest.fixture
def use_overlay(monkeypatch):
    def _use(root: Path) -> Path:
        monkeypatch.setenv(be.BENCHMARK_EXTENSIONS_DIR_ENV, str(root))
        return root

    return _use


# --------------------------------------------------------------------- config overlay


def test_valid_config_overlay_is_still_merged(tmp_path, use_overlay):
    root = _write_overlay(
        tmp_path / "ext",
        config={
            "connectors_configurations": [
                {"id": "ext-conn", "connector_adapter": "openai_adapter"}
            ]
        },
    )
    use_overlay(root)

    assert AppConfig().get_connector_config("ext-conn") is not None
    assert be.resolve_extensions_dir() == root.resolve()
    assert be.get_invalid_extensions() == {}


def test_duplicate_metric_in_overlay_config_keeps_builtin_config(tmp_path, use_overlay):
    root = _write_overlay(
        tmp_path / "ext",
        config={"metrics": [{"name": "accuracy_adapter"}]},
    )
    use_overlay(root)

    config = AppConfig()

    assert config.get_metric_config("refusal_adapter") is not None
    assert config.get_metric_config("accuracy_adapter") is not None
    assert [m["name"] for m in config.config.metrics].count("accuracy_adapter") == 1
    assert be.resolve_extensions_dir() is None
    assert str(root.resolve()) in be.get_invalid_extensions()


def test_malformed_overlay_config_keeps_builtin_config(tmp_path, use_overlay):
    root = _write_overlay(tmp_path / "ext", config="metrics: [unclosed\n")
    use_overlay(root)

    assert AppConfig().get_metric_config("refusal_adapter") is not None
    assert be.resolve_extensions_dir() is None


def test_dataset_id_collision_keeps_builtin_config(tmp_path, use_overlay):
    builtin_id = sorted((MOONSHOT_CORE_ROOT / "data" / "datasets").glob("*.json"))[0].stem
    root = _write_overlay(
        tmp_path / "ext",
        config={
            "connectors_configurations": [
                {"id": "ext-conn", "connector_adapter": "openai_adapter"}
            ]
        },
        datasets=(builtin_id,),
    )
    use_overlay(root)

    config = AppConfig()

    assert config.get_metric_config("refusal_adapter") is not None
    assert config.get_connector_config("ext-conn") is None
    assert be.resolve_extensions_dir() is None


def test_invalid_overlay_disables_adapter_and_dataset_hooks(tmp_path, use_overlay):
    root = _write_overlay(
        tmp_path / "ext",
        config={"metrics": [{"name": "accuracy_adapter"}]},
        datasets=("ext_only",),
        metric_adapters=("ext_metric_adapter",),
    )
    use_overlay(root)

    AppConfig()  # marks the overlay invalid

    assert be.resolve_adapter_module_path(ModuleTypes.METRIC, "ext_metric_adapter") == (
        os.path.join(be.BUILTIN_ADAPTERS_REL, "metric", "ext_metric_adapter.py")
    )
    paths = be.get_dataset_search_paths()
    assert len(paths) == 1
    assert str(root) not in paths[0]


# ----------------------------------------------------------------------- seed overlay


class _FakeMoonshotConfig:
    """Dict-backed stand-in for MoonshotConfigAdapter (get_by_key / set)."""

    def __init__(self):
        self.values: dict[str, str] = {}

    def get_by_key(self, key):
        value = self.values.get(key)
        if value is None:
            return None
        return MoonshotConfigEntity(id=1, key=key, value=value)

    def set(self, key, value):
        self.values[key] = value


BASE_CONFIG = {
    "base-bundle": {
        "name": "Base",
        "tests": [
            {"name": "Base", "dataset": "base_ds", "metric": {"name": "accuracy_adapter"}}
        ],
    }
}


@pytest.fixture
def base_path(tmp_path):
    path = tmp_path / "shared.yaml"
    path.write_text("base: {}\n")
    return path


@pytest.fixture
def moonshot_config():
    return _FakeMoonshotConfig()


def _make_service(moonshot_config, base_path):
    shared_repo = MagicMock()
    shared_repo.get_last_modified.return_value = base_path.stat().st_mtime
    shared_repo.get_config.return_value = dict(BASE_CONFIG)
    service = SharedConfigSeedService(
        adapter=MagicMock(),
        moonshot_config_repository=moonshot_config,
        shared_config_repository=shared_repo,
        benchmark_dataset_seed_service=MagicMock(),
    )
    service._seed_from_data = MagicMock()
    return service


def _seeded_keys(service) -> set[str]:
    return set(service._seed_from_data.call_args[0][0])


def test_seed_with_duplicate_bundle_key_seeds_builtin_only(
    tmp_path, use_overlay, moonshot_config, base_path
):
    root = _write_overlay(
        tmp_path / "ext",
        shared={"base-bundle": _bundle("ext_ds")},
        datasets=("ext_ds",),
    )
    use_overlay(root)
    service = _make_service(moonshot_config, base_path)

    assert service.seed_if_test_file_changed(config_path=base_path) is True

    assert _seeded_keys(service) == {"base-bundle"}
    service._dataset_seed_service.seed_benchmark_dataset.assert_called_once_with("base_ds")
    assert be.resolve_extensions_dir() is None


def test_seed_with_missing_dataset_seeds_builtin_only(
    tmp_path, use_overlay, moonshot_config, base_path
):
    root = _write_overlay(tmp_path / "ext", shared={"ext-bundle": _bundle("not_there")})
    use_overlay(root)
    service = _make_service(moonshot_config, base_path)

    assert service.seed_if_test_file_changed(config_path=base_path) is True

    assert _seeded_keys(service) == {"base-bundle"}
    assert be.resolve_extensions_dir() is None


def test_seed_with_test_missing_metric_name_seeds_builtin_only(
    tmp_path, use_overlay, moonshot_config, base_path
):
    bundle = {"name": "Ext", "tests": [{"name": "T", "dataset": "ext_ds", "metric": {}}]}
    root = _write_overlay(tmp_path / "ext", shared={"ext-bundle": bundle}, datasets=("ext_ds",))
    use_overlay(root)
    service = _make_service(moonshot_config, base_path)

    assert service.seed_if_test_file_changed(config_path=base_path) is True

    assert _seeded_keys(service) == {"base-bundle"}


def test_seed_with_valid_overlay_still_merges(
    tmp_path, use_overlay, moonshot_config, base_path
):
    root = _write_overlay(
        tmp_path / "ext",
        shared={"ext-bundle": _bundle("ext_ds")},
        datasets=("ext_ds",),
    )
    use_overlay(root)
    service = _make_service(moonshot_config, base_path)

    assert service.seed_if_test_file_changed(config_path=base_path) is True

    assert _seeded_keys(service) == {"base-bundle", "ext-bundle"}
    assert be.resolve_extensions_dir() == root.resolve()


def test_seed_dropping_overlay_also_drops_config_already_merged_by_app_config(
    tmp_path, use_overlay, moonshot_config, base_path
):
    """Config is valid but the overlay's bundle is not: nothing from the overlay survives."""
    root = _write_overlay(
        tmp_path / "ext",
        shared={"ext-bundle": _bundle("not_there")},
        config={
            "connectors_configurations": [
                {"id": "ext-conn", "connector_adapter": "openai_adapter"}
            ]
        },
    )
    use_overlay(root)
    config = AppConfig()
    assert config.get_connector_config("ext-conn") is not None
    service = _make_service(moonshot_config, base_path)

    service.seed_if_test_file_changed(config_path=base_path)

    assert AppConfig() is config
    assert config.get_connector_config("ext-conn") is None
    assert config.get_metric_config("refusal_adapter") is not None


def test_unchanged_invalid_overlay_does_not_reseed_on_restart(
    tmp_path, use_overlay, moonshot_config, base_path
):
    root = _write_overlay(tmp_path / "ext", shared={"ext-bundle": _bundle("not_there")})
    use_overlay(root)
    first = _make_service(moonshot_config, base_path)
    assert first.seed_if_test_file_changed(config_path=base_path) is True

    be.reset_invalid_extensions()  # a restart forgets the in-process mark
    second = _make_service(moonshot_config, base_path)

    assert second.seed_if_test_file_changed(config_path=base_path) is False
    second._seed_from_data.assert_not_called()
    # The skipped seed still re-decides the overlay, so nothing is half-applied.
    assert be.resolve_extensions_dir() is None


def test_fixed_overlay_is_picked_up_on_next_restart(
    tmp_path, use_overlay, moonshot_config, base_path
):
    root = _write_overlay(tmp_path / "ext", shared={"ext-bundle": _bundle("ext_ds")})
    use_overlay(root)
    first = _make_service(moonshot_config, base_path)
    assert first.seed_if_test_file_changed(config_path=base_path) is True
    assert _seeded_keys(first) == {"base-bundle"}

    _write_overlay(root, datasets=("ext_ds",))  # the fix is only a new dataset file
    be.reset_invalid_extensions()  # restart
    second = _make_service(moonshot_config, base_path)

    assert second.seed_if_test_file_changed(config_path=base_path) is True
    assert _seeded_keys(second) == {"base-bundle", "ext-bundle"}
    assert be.resolve_extensions_dir() == root.resolve()


def test_overlay_edited_after_being_dropped_is_not_applied_until_restart(
    tmp_path, use_overlay, moonshot_config, base_path
):
    root = _write_overlay(tmp_path / "ext", shared={"ext-bundle": _bundle("ext_ds")})
    use_overlay(root)
    service = _make_service(moonshot_config, base_path)
    service.seed_if_test_file_changed(config_path=base_path)
    fingerprint = be.compute_shared_config_fingerprint(base_path)

    _write_overlay(root, datasets=("ext_ds",))  # fixed while the process keeps running

    assert be.resolve_extensions_dir() is None
    assert be.compute_shared_config_fingerprint(base_path) == fingerprint
    assert service.seed_if_test_file_changed(config_path=base_path) is False


def test_errors_in_the_builtin_config_are_not_swallowed(
    tmp_path, use_overlay, moonshot_config, base_path
):
    root = _write_overlay(
        tmp_path / "ext",
        shared={"ext-bundle": _bundle("ext_ds")},
        datasets=("ext_ds",),
    )
    use_overlay(root)
    service = _make_service(moonshot_config, base_path)
    service._shared_config_repo.get_config.side_effect = ValueError("broken built-in")

    with pytest.raises(ValueError, match="broken built-in"):
        service.seed_if_test_file_changed(config_path=base_path)


# ---------------------------------------------------------------- validate_overlay_bundles


def test_validate_overlay_bundles_accepts_builtin_dataset(tmp_path):
    builtin = tmp_path / "builtin"
    builtin.mkdir()
    (builtin / "shared_ds.json").write_text("{}")
    root = tmp_path / "ext"
    root.mkdir()

    be.validate_overlay_bundles({"b": _bundle("shared_ds")}, root, builtin)


def test_validate_overlay_bundles_rejects_missing_dataset(tmp_path):
    builtin = tmp_path / "builtin"
    builtin.mkdir()
    root = tmp_path / "ext"
    root.mkdir()

    with pytest.raises(be.BenchmarkExtensionError, match="references dataset"):
        be.validate_overlay_bundles({"b": _bundle("nope")}, root, builtin)


def test_validate_overlay_bundles_rejects_test_without_dataset(tmp_path):
    bundle = {"tests": [{"name": "T", "metric": {"name": "accuracy_adapter"}}]}
    with pytest.raises(be.BenchmarkExtensionError, match="no 'dataset'"):
        be.validate_overlay_bundles({"b": bundle}, tmp_path, tmp_path)
