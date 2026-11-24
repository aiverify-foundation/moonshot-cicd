"""Benchmark extensions: merge user overlays and resolve extension paths."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from domain.entities.app_config_entity import AppConfigEntity
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.enums.module_types import ModuleTypes
from domain.services.feature_flags import FeatureFlags
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

BENCHMARK_EXTENSIONS_DIR_ENV = "MOONSHOT_BENCHMARK_EXTENSIONS_DIR"
LOCAL_BENCHMARK_EXTENSIONS_DIRNAME = "benchmark-extensions"
DOCKER_DATA_DIR = Path("/var/lib/moonshot")
SHARED_CONFIG_SEED_FINGERPRINT_KEY = "shared_config_seed_fingerprint"

EXTENSION_MOONSHOT_CONFIG = "moonshot_config.yaml"
EXTENSION_SHARED_CONFIG = "test_configs/shared.yaml"
EXTENSION_DATASETS_DIR = "datasets"
EXTENSION_ADAPTERS_DIR = "adapters"
BUILTIN_DATASETS_REL = "data/datasets"
BUILTIN_ADAPTERS_REL = "src/adapters"


class BenchmarkExtensionError(ValueError):
    """Invalid or conflicting benchmark extension content."""


class AdapterNotFoundError(FileNotFoundError):
    """
    A metric or connector adapter file that a run needs is not on disk.

    ``str(exc)`` is the full message, including file paths, and is meant for logs. Callers
    that report to a client use ``module_type`` and ``adapter_name`` instead, so paths on
    the server are not sent out.
    """

    def __init__(
        self,
        message: str,
        *,
        module_type: Optional[ModuleTypes] = None,
        adapter_name: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.module_type = module_type
        self.adapter_name = adapter_name


# Errors that mean "the overlay is unusable". Anything else (for example a broken
# built-in config) is not an overlay problem and must not be swallowed.
OVERLAY_ERRORS: tuple[type[BaseException], ...] = (
    BenchmarkExtensionError,
    yaml.YAMLError,
    OSError,
    UnicodeError,
)


@dataclass(frozen=True)
class InvalidExtensionsOverlay:
    """An overlay that was judged unusable in this process."""

    reason: str
    # Overlay file state when it was judged. Used for the seed fingerprint so an
    # unchanged invalid overlay does not reseed on every restart, while a fixed
    # (changed) overlay does.
    signature: tuple[str, ...]


# Overlays marked invalid in this process, keyed by resolved directory. The mark is
# never cleared at runtime: the overlay is decided once per process and re-evaluated
# on restart (see ``reset_invalid_extensions`` for tests).
_INVALID_EXTENSIONS: dict[Path, InvalidExtensionsOverlay] = {}

# (extensions dir, adapter type dir, file name) already reported as shadowed by a built-in
# adapter, so the error is logged once per adapter and not on every load.
_REPORTED_ADAPTER_COLLISIONS: set[tuple[str, str, str]] = set()


def get_application_root() -> Path:
    from application.services.utils import get_application_root_path

    return get_application_root_path()


def benchmark_extensions_enabled() -> bool:
    """Return True when benchmark-extensions overlays are allowed (MOON807)."""
    return FeatureFlags().is_enabled(FeatureFlagNames.AIVET_OCT2026_MOON807)


def _raw_extensions_dir() -> Optional[Path]:
    """
    Return the configured extensions directory, ignoring whether it was marked invalid.

    Requires AIVET_OCT2026_MOON807. Order:
    1. MOONSHOT_BENCHMARK_EXTENSIONS_DIR when set (returns None if it is not a directory).
    2. ``/var/lib/moonshot/benchmark-extensions`` when that directory exists (Docker data volume).
    3. Otherwise None. There is no app-root fallback.
    """
    if not benchmark_extensions_enabled():
        return None

    env_path = os.getenv(BENCHMARK_EXTENSIONS_DIR_ENV, "").strip()
    if env_path:
        path = Path(env_path).resolve()
        return path if path.is_dir() else None

    volume_dir = DOCKER_DATA_DIR / LOCAL_BENCHMARK_EXTENSIONS_DIRNAME
    if volume_dir.is_dir():
        return volume_dir.resolve()
    return None


def resolve_extensions_dir() -> Optional[Path]:
    """
    Return the benchmark extensions root directory, or None if extensions are not in use.

    This is the single switch every overlay hook goes through (config merge, seed merge,
    dataset search, adapter resolution). It returns None when MOON807 is off, when no
    directory is configured, or when the overlay was marked invalid in this process
    (``mark_extensions_invalid``). A directory is therefore either used by all hooks or
    by none, so an invalid overlay can never be half-applied.
    """
    extensions_dir = _raw_extensions_dir()
    if extensions_dir is None or extensions_dir in _INVALID_EXTENSIONS:
        return None
    return extensions_dir


def mark_extensions_invalid(
    extensions_dir: Path,
    reason: str,
    *,
    reload_app_config: bool = True,
) -> None:
    """
    Stop using the overlay at ``extensions_dir`` for the rest of this process.

    Built-in benchmarks, datasets, adapters and config are used instead. The overlay is
    re-evaluated on the next restart. When ``reload_app_config`` is true and AppConfig
    was already built with this overlay merged in, it is rebuilt from the built-in config.
    Pass False when the caller is AppConfig itself (it is already returning the base).
    """
    key = Path(extensions_dir).resolve()
    _INVALID_EXTENSIONS[key] = InvalidExtensionsOverlay(
        reason=reason,
        signature=tuple(_overlay_signature(key)),
    )
    logger.error(
        "Ignoring benchmark extensions overlay at %s: %s. Built-in benchmarks, datasets, "
        "adapters and config are used instead. Fix the overlay and restart the API to "
        "re-enable it.",
        key,
        reason,
    )
    if reload_app_config:
        _reload_app_config_without_overlay()


def get_invalid_extensions() -> dict[str, str]:
    """Return ``{overlay directory: reason}`` for overlays ignored in this process."""
    return {str(path): info.reason for path, info in _INVALID_EXTENSIONS.items()}


def reset_invalid_extensions() -> None:
    """Forget invalid-overlay marks (for tests; production re-evaluates on restart)."""
    _INVALID_EXTENSIONS.clear()
    _REPORTED_ADAPTER_COLLISIONS.clear()


def _reload_app_config_without_overlay() -> None:
    """Rebuild the AppConfig singleton in place so cached overlay entries are dropped."""
    from domain.services.app_config import AppConfig

    instance = AppConfig._instance
    if instance is None or instance._config is None:
        return
    try:
        instance._initialize()
    except Exception as exc:  # noqa: BLE001 - never let a reload break the caller
        logger.error(
            "Could not reload app config without the extensions overlay: %s", exc
        )


def extensions_moonshot_config_path(extensions_dir: Path) -> Path:
    return extensions_dir / EXTENSION_MOONSHOT_CONFIG


def extensions_shared_config_path(extensions_dir: Path) -> Path:
    return extensions_dir / EXTENSION_SHARED_CONFIG


def extensions_datasets_dir(extensions_dir: Path) -> Path:
    return extensions_dir / EXTENSION_DATASETS_DIR


def extensions_adapter_dir(extensions_dir: Path, module_type: ModuleTypes) -> Path:
    sub = module_type.name.lower()
    return extensions_dir / EXTENSION_ADAPTERS_DIR / sub


def load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise BenchmarkExtensionError(
            f"Expected top-level dict in {path}, got {type(data).__name__}"
        )
    return data


def merge_app_config_entity(
    base: AppConfigEntity, overlay: dict[str, Any]
) -> AppConfigEntity:
    """Append overlay fragments onto base; reject duplicates."""
    merged = base.model_copy(deep=True)

    overlay_common = overlay.get("common")
    if overlay_common is not None:
        if not isinstance(overlay_common, dict):
            raise BenchmarkExtensionError("'common' in extension config must be a mapping")
        for key, value in overlay_common.items():
            if key in merged.common:
                raise BenchmarkExtensionError(
                    f"Extension moonshot_config common key {key!r} conflicts with built-in config"
                )
            merged.common[key] = value

    merged.connectors_configurations = _append_by_key(
        merged.connectors_configurations,
        overlay.get("connectors_configurations"),
        key_field="id",
        section="connectors_configurations",
    )
    merged.metrics = _append_by_key(
        merged.metrics,
        overlay.get("metrics"),
        key_field="name",
        section="metrics",
    )
    merged.attack_modules = _append_by_key(
        merged.attack_modules,
        overlay.get("attack_modules"),
        key_field="name",
        section="attack_modules",
    )
    return merged


def _append_by_key(
    base_list: list[dict[str, Any]],
    overlay_items: Any,
    key_field: str,
    section: str,
) -> list[dict[str, Any]]:
    if overlay_items is None:
        return base_list
    if not isinstance(overlay_items, list):
        raise BenchmarkExtensionError(f"Extension {section} must be a list")

    existing = {
        item.get(key_field)
        for item in base_list
        if isinstance(item, dict) and item.get(key_field) is not None
    }
    result = list(base_list)
    for item in overlay_items:
        if not isinstance(item, dict):
            raise BenchmarkExtensionError(f"Each entry in extension {section} must be a mapping")
        key = item.get(key_field)
        if not key:
            raise BenchmarkExtensionError(
                f"Extension {section} entry missing required {key_field!r}"
            )
        if key in existing:
            raise BenchmarkExtensionError(
                f"Extension {section} duplicates built-in {key_field}={key!r}"
            )
        existing.add(key)
        result.append(item)
    return result


def merge_shared_config(
    base: dict[str, Any], overlay: dict[str, Any]
) -> dict[str, Any]:
    """Merge shared.yaml bundle keys; reject duplicate bundle keys."""
    merged = dict(base)
    for key, value in overlay.items():
        if key in merged:
            raise BenchmarkExtensionError(
                f"Extension shared.yaml duplicates built-in bundle key {key!r}"
            )
        merged[key] = value
    return merged


def load_merged_shared_config(base_path: Path) -> dict[str, Any]:
    """Load built-in shared.yaml and merge optional extension fragment."""
    base = load_yaml_dict(base_path)
    extensions_dir = resolve_extensions_dir()
    if extensions_dir is None:
        return base
    ext_path = extensions_shared_config_path(extensions_dir)
    if not ext_path.is_file():
        return base
    overlay = load_yaml_dict(ext_path)
    return merge_shared_config(base, overlay)


def _file_signature(label: str, path: Path) -> str:
    stat = path.stat()
    return f"{label}:{stat.st_mtime_ns}:{stat.st_size}"


def _overlay_signature(extensions_dir: Path) -> list[str]:
    """
    Describe the overlay files that decide whether the overlay is valid.

    ``ext:`` is the overlay shared.yaml (``ext:none`` when absent). The overlay
    moonshot_config.yaml and the dataset files are added only when present, so a fix to
    any of them changes the fingerprint and triggers a reseed on the next restart.
    """
    shared_path = extensions_shared_config_path(extensions_dir)
    parts = [
        _file_signature("ext", shared_path) if shared_path.is_file() else "ext:none"
    ]

    config_path = extensions_moonshot_config_path(extensions_dir)
    if config_path.is_file():
        parts.append(_file_signature("extcfg", config_path))

    datasets_dir = extensions_datasets_dir(extensions_dir)
    if datasets_dir.is_dir():
        dataset_files = sorted(p for p in datasets_dir.glob("*.json") if p.is_file())
        if dataset_files:
            listing = ";".join(
                f"{p.name}:{p.stat().st_mtime_ns}:{p.stat().st_size}"
                for p in dataset_files
            )
            parts.append("extds:" + hashlib.sha256(listing.encode()).hexdigest())
    return parts


def _fingerprint_extension_parts() -> list[str]:
    extensions_dir = resolve_extensions_dir()
    if extensions_dir is not None:
        return _overlay_signature(extensions_dir)

    raw_dir = _raw_extensions_dir()
    invalid = _INVALID_EXTENSIONS.get(raw_dir) if raw_dir is not None else None
    if invalid is not None:
        # Overlay is being ignored: record the state it was judged in, not its current
        # state, so the next restart reseeds only if the overlay changed since.
        return list(invalid.signature)
    return ["ext:none"]


def compute_shared_config_fingerprint(base_path: Path) -> str:
    """
    Fingerprint for change detection: base shared.yaml plus optional extension overlay.
    """
    parts: list[str] = []
    if base_path.is_file():
        stat = base_path.stat()
        parts.append(f"base:{stat.st_mtime_ns}:{stat.st_size}")
    else:
        parts.append("base:missing")

    parts.extend(_fingerprint_extension_parts())

    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return digest


def validate_extension_dataset_ids(extensions_dir: Path, builtin_datasets_dir: Path) -> None:
    """Reject extension datasets whose id (stem) collides with a built-in dataset file."""
    ext_dir = extensions_datasets_dir(extensions_dir)
    if not ext_dir.is_dir():
        return
    builtin_ids = {
        p.stem for p in builtin_datasets_dir.glob("*.json") if p.is_file()
    }
    for path in ext_dir.glob("*.json"):
        if path.stem in builtin_ids:
            raise BenchmarkExtensionError(
                f"Extension dataset {path.name!r} duplicates built-in dataset id {path.stem!r}"
            )


def validate_overlay_bundles(
    overlay: dict[str, Any],
    extensions_dir: Path,
    builtin_datasets_dir: Path,
) -> None:
    """
    Reject overlay bundles the seed could not load, before anything is written.

    Checks only the structure the seed would otherwise fail on (a test without a dataset
    or metric name) and that every referenced dataset file exists in the overlay or in
    the built-in datasets. Failing here lets the caller drop the whole overlay instead
    of failing midway through seeding.
    """
    ext_datasets = extensions_datasets_dir(extensions_dir)
    for bundle_key, bundle in overlay.items():
        if not isinstance(bundle, dict):
            continue
        tests = bundle.get("tests")
        if not tests:
            continue
        if not isinstance(tests, list):
            raise BenchmarkExtensionError(
                f"Extension bundle {bundle_key!r} 'tests' must be a list"
            )
        for test in tests:
            if not isinstance(test, dict) or not test.get("name"):
                continue
            label = f"Extension bundle {bundle_key!r} test {test['name']!r}"
            dataset = test.get("dataset")
            if not dataset or not isinstance(dataset, str):
                raise BenchmarkExtensionError(f"{label} has no 'dataset'")
            metric = test.get("metric")
            if not isinstance(metric, dict) or not metric.get("name"):
                raise BenchmarkExtensionError(f"{label} has no 'metric.name'")
            filename = f"{dataset}.json"
            if (
                not (ext_datasets / filename).is_file()
                and not (builtin_datasets_dir / filename).is_file()
            ):
                raise BenchmarkExtensionError(
                    f"{label} references dataset {dataset!r}, which is in neither "
                    f"{ext_datasets} nor {builtin_datasets_dir}"
                )


def get_dataset_search_paths() -> list[str]:
    """Search extension datasets first, then built-in data/datasets."""
    paths: list[str] = []
    extensions_dir = resolve_extensions_dir()
    if extensions_dir is not None:
        ext_datasets = extensions_datasets_dir(extensions_dir)
        if ext_datasets.is_dir():
            paths.append(str(ext_datasets) + "/")

    root = get_application_root()
    builtin = root / BUILTIN_DATASETS_REL
    paths.append(str(builtin) + "/")
    return paths


def _builtin_adapter_file(type_dirname: str, filename: str) -> Path:
    """Absolute path of a built-in adapter file, for existence checks only."""
    return get_application_root() / BUILTIN_ADAPTERS_REL / type_dirname / filename


def _report_adapter_collision(
    extensions_dir: Path, type_dirname: str, filename: str
) -> None:
    """Log (once per process and adapter) that a built-in adapter shadows an overlay one."""
    key = (str(extensions_dir), type_dirname, filename)
    if key in _REPORTED_ADAPTER_COLLISIONS:
        return
    _REPORTED_ADAPTER_COLLISIONS.add(key)
    logger.error(
        "Extension adapter %s has the same name as built-in adapter %s. The built-in "
        "adapter is used and the extension adapter is ignored. Rename the extension "
        "adapter file to use it.",
        extensions_dir / EXTENSION_ADAPTERS_DIR / type_dirname / filename,
        _builtin_adapter_file(type_dirname, filename),
    )


def find_adapter_collisions(extensions_dir: Path) -> list[Path]:
    """
    Return overlay adapter files that share a name with a built-in adapter.

    Looks at ``<ext>/adapters/<type>/*.py`` against ``src/adapters/<type>/``. Such files
    are ignored at load time because the built-in adapter has precedence.
    """
    adapters_root = extensions_dir / EXTENSION_ADAPTERS_DIR
    if not adapters_root.is_dir():
        return []
    collisions: list[Path] = []
    for type_dir in sorted(p for p in adapters_root.iterdir() if p.is_dir()):
        for adapter_file in sorted(type_dir.glob("*.py")):
            if _builtin_adapter_file(type_dir.name, adapter_file.name).is_file():
                collisions.append(adapter_file)
    return collisions


def report_adapter_collisions(extensions_dir: Path) -> None:
    """Log an error for every overlay adapter that a built-in adapter shadows."""
    try:
        collisions = find_adapter_collisions(extensions_dir)
    except OSError as exc:
        logger.warning("Could not scan extension adapters for name collisions: %s", exc)
        return
    for adapter_file in collisions:
        _report_adapter_collision(
            extensions_dir, adapter_file.parent.name, adapter_file.name
        )


def resolve_adapter_module_path(module_type: ModuleTypes, loader_name: str) -> str:
    """
    Resolve metric/connector adapter module path.

    A built-in adapter always has precedence. An overlay adapter is used only when no
    built-in adapter has the same name; when both exist the built-in path is returned and
    an error is logged (once per adapter).
    """
    filename = f"{loader_name}.py"
    type_dirname = module_type.name.lower()
    builtin_path = os.path.join(BUILTIN_ADAPTERS_REL, type_dirname, filename)

    extensions_dir = resolve_extensions_dir()
    if extensions_dir is not None:
        ext_path = extensions_adapter_dir(extensions_dir, module_type) / filename
        if ext_path.is_file():
            if _builtin_adapter_file(type_dirname, filename).is_file():
                _report_adapter_collision(extensions_dir, type_dirname, filename)
                return builtin_path
            return str(ext_path)

    return builtin_path


def adapter_not_found_error(
    module_type: ModuleTypes, loader_name: str
) -> AdapterNotFoundError:
    """
    Build the error for a metric/connector adapter whose file is missing.

    The message names the adapter and every location that was checked, and says when the
    extensions directory is not in use, so an operator can tell a missing overlay file
    from an overlay that was never applied.
    """
    type_dirname = module_type.name.lower()
    filename = f"{loader_name}.py"
    message = (
        f"{type_dirname} adapter {loader_name!r} not found: no file at "
        f"{_builtin_adapter_file(type_dirname, filename)}"
    )
    extensions_dir = resolve_extensions_dir()
    if extensions_dir is None:
        message += (
            ". The benchmark extensions directory is not in use (flag off, no directory "
            "configured, or overlay ignored), so only built-in adapters were checked."
        )
    else:
        ext_path = extensions_adapter_dir(extensions_dir, module_type) / filename
        message += f". The extensions directory was also checked at {ext_path}."
    return AdapterNotFoundError(
        message, module_type=module_type, adapter_name=loader_name
    )


def ensure_adapter_available(module_type: ModuleTypes, loader_name: str) -> str:
    """
    Return the adapter path that would be loaded, or raise AdapterNotFoundError.

    Existence check only (``os.path.exists``). It does not import the module, so it is
    meant for preflight checks that run before any database row is changed.
    """
    path = resolve_adapter_module_path(module_type, loader_name)
    if not os.path.exists(path):
        raise adapter_not_found_error(module_type, loader_name)
    return path


def apply_app_config_extensions(base_config: AppConfigEntity) -> AppConfigEntity:
    """
    Load optional extension moonshot_config.yaml and merge onto base.
    Validates extension dataset ids do not collide with built-in datasets.

    An unusable overlay (duplicate ids, malformed YAML, dataset id collision) is dropped
    for the whole process: the overlay is marked invalid and the unchanged built-in
    config is returned, so the built-in benchmarks keep working.
    """
    extensions_dir = resolve_extensions_dir()
    if extensions_dir is None:
        return base_config

    # Surface adapter name collisions at startup. The built-in adapter wins, so this is
    # not a reason to drop the overlay.
    report_adapter_collisions(extensions_dir)

    config_path = extensions_moonshot_config_path(extensions_dir)
    try:
        validate_extension_dataset_ids(
            extensions_dir,
            get_application_root() / BUILTIN_DATASETS_REL,
        )
        if not config_path.is_file():
            return base_config
        overlay = load_yaml_dict(config_path)
        merged = merge_app_config_entity(base_config, overlay)
    except OVERLAY_ERRORS as exc:
        mark_extensions_invalid(
            extensions_dir,
            f"moonshot_config.yaml overlay is unusable: {exc}",
            reload_app_config=False,
        )
        return base_config

    logger.info("Merging benchmark extension config from %s", config_path)
    return merged
