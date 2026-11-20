"""Benchmark extensions: merge user overlays and resolve extension paths."""

from __future__ import annotations

import hashlib
import os
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
SHARED_CONFIG_SEED_FINGERPRINT_KEY = "shared_config_seed_fingerprint"

EXTENSION_MOONSHOT_CONFIG = "moonshot_config.yaml"
EXTENSION_SHARED_CONFIG = "test_configs/shared.yaml"
EXTENSION_DATASETS_DIR = "datasets"
EXTENSION_ADAPTERS_DIR = "adapters"
BUILTIN_DATASETS_REL = "data/datasets"
BUILTIN_ADAPTERS_REL = "src/adapters"


class BenchmarkExtensionError(ValueError):
    """Invalid or conflicting benchmark extension content."""


def get_application_root() -> Path:
    from application.services.utils import get_application_root_path

    return get_application_root_path()


def benchmark_extensions_enabled() -> bool:
    """Return True when benchmark-extensions overlays are allowed (MOON807)."""
    return FeatureFlags().is_enabled(FeatureFlagNames.AIVET_OCT2026_MOON807)


def resolve_extensions_dir() -> Optional[Path]:
    """
    Return the benchmark extensions root directory, or None if extensions are disabled.

    Requires AIVET_OCT2026_MOON807. Uses MOONSHOT_BENCHMARK_EXTENSIONS_DIR when set;
    otherwise ``{app_root}/benchmark-extensions`` when that directory exists.
    """
    if not benchmark_extensions_enabled():
        return None

    env_path = os.getenv(BENCHMARK_EXTENSIONS_DIR_ENV, "").strip()
    if env_path:
        path = Path(env_path).resolve()
        return path if path.is_dir() else None

    default = get_application_root() / LOCAL_BENCHMARK_EXTENSIONS_DIRNAME
    if default.is_dir():
        return default.resolve()
    return None


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


def compute_shared_config_fingerprint(base_path: Path) -> str:
    """
    Fingerprint for change detection: base shared.yaml plus optional extension fragment.
    """
    parts: list[str] = []
    if base_path.is_file():
        stat = base_path.stat()
        parts.append(f"base:{stat.st_mtime_ns}:{stat.st_size}")
    else:
        parts.append("base:missing")

    extensions_dir = resolve_extensions_dir()
    ext_path = (
        extensions_shared_config_path(extensions_dir)
        if extensions_dir is not None
        else None
    )
    if ext_path is not None and ext_path.is_file():
        stat = ext_path.stat()
        parts.append(f"ext:{stat.st_mtime_ns}:{stat.st_size}")
    else:
        parts.append("ext:none")

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


def resolve_adapter_module_path(module_type: ModuleTypes, loader_name: str) -> str:
    """
    Resolve metric/connector adapter module path; extension adapters take precedence.
    """
    filename = f"{loader_name}.py"
    extensions_dir = resolve_extensions_dir()
    if extensions_dir is not None:
        ext_path = extensions_adapter_dir(extensions_dir, module_type) / filename
        if ext_path.is_file():
            return str(ext_path)

    return os.path.join(
        BUILTIN_ADAPTERS_REL,
        module_type.name.lower(),
        filename,
    )


def apply_app_config_extensions(base_config: AppConfigEntity) -> AppConfigEntity:
    """
    Load optional extension moonshot_config.yaml and merge onto base.
    Validates extension dataset ids do not collide with built-in datasets.
    """
    extensions_dir = resolve_extensions_dir()
    if extensions_dir is None:
        return base_config

    validate_extension_dataset_ids(
        extensions_dir,
        get_application_root() / BUILTIN_DATASETS_REL,
    )

    config_path = extensions_moonshot_config_path(extensions_dir)
    if not config_path.is_file():
        return base_config

    overlay = load_yaml_dict(config_path)
    logger.info("Merging benchmark extension config from %s", config_path)
    return merge_app_config_entity(base_config, overlay)
