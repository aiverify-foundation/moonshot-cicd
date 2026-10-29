"""
Append non-fatal shared-config validation warnings to a dedicated log file.

Path precedence: ``MS_STARTUP_CONFIG_WARNINGS_LOG_PATH``, then
``$MOONSHOT_BENCHMARK_RESULTS_DIR/startup_config_warnings.log`` (Docker:
``/var/lib/moonshot/results/startup_config_warnings.log`` on the mounted volume),
then ``data/results/startup_config_warnings.log``.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domain.services.logger import configure_file_logger, configure_logger

logger = configure_logger(__name__)

STARTUP_CONFIG_WARNINGS_FILENAME = "startup_config_warnings.log"
DEFAULT_STARTUP_CONFIG_WARNINGS_LOG_PATH = "data/results/startup_config_warnings.log"
STARTUP_CONFIG_WARNINGS_LOGGER_NAME = f"{__name__}.file"


@dataclass(frozen=True)
class TestNameOccurrence:
    bundle_key: str
    bundle_display_name: str


@dataclass(frozen=True)
class DuplicateTestDisplayName:
    test_name: str
    occurrences: tuple[TestNameOccurrence, ...]


def resolve_startup_config_warnings_log_path() -> Path:
    explicit_path = os.getenv("MS_STARTUP_CONFIG_WARNINGS_LOG_PATH")
    if explicit_path:
        log_path: str | Path = explicit_path
    elif results_dir := os.getenv("MOONSHOT_BENCHMARK_RESULTS_DIR"):
        log_path = Path(results_dir) / STARTUP_CONFIG_WARNINGS_FILENAME
    else:
        log_path = DEFAULT_STARTUP_CONFIG_WARNINGS_LOG_PATH
    file_path = Path(log_path)
    if file_path.suffix == "":
        file_path = file_path.with_suffix(".log")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path.resolve()


def find_duplicate_test_display_names(
    config: dict[str, Any],
) -> list[DuplicateTestDisplayName]:
    """Return groups where the same test display ``name`` appears more than once globally."""
    by_name: dict[str, list[TestNameOccurrence]] = defaultdict(list)
    for bundle_key, bundle_data in config.items():
        if not isinstance(bundle_data, dict):
            continue
        bundle_display_name = bundle_data.get("name", bundle_key)
        if not isinstance(bundle_display_name, str):
            bundle_display_name = str(bundle_display_name)
        for test in bundle_data.get("tests") or []:
            if not isinstance(test, dict):
                continue
            test_name = test.get("name")
            if not test_name or not isinstance(test_name, str):
                continue
            by_name[test_name].append(
                TestNameOccurrence(
                    bundle_key=str(bundle_key),
                    bundle_display_name=bundle_display_name,
                )
            )

    duplicates: list[DuplicateTestDisplayName] = []
    for test_name, occurrences in sorted(by_name.items()):
        if len(occurrences) < 2:
            continue
        duplicates.append(
            DuplicateTestDisplayName(
                test_name=test_name,
                occurrences=tuple(occurrences),
            )
        )
    return duplicates


def log_startup_config_warning(record: dict[str, Any]) -> None:
    """Append one warning record to the startup config warnings log. Never raises."""
    try:
        block = (
            "\n"
            + "=" * 72
            + "\n"
            + json.dumps(record, indent=2, ensure_ascii=False, default=str)
            + "\n"
        )
        warnings_logger = configure_file_logger(
            STARTUP_CONFIG_WARNINGS_LOGGER_NAME,
            resolve_startup_config_warnings_log_path(),
        )
        warnings_logger.error(block)
    except Exception as write_error:
        logger.warning(
            "[startup_config_warnings] Failed to write startup config warning: %s",
            write_error,
        )


def report_duplicate_test_display_names(
    config: dict[str, Any],
    config_source: str | Path | None = None,
) -> None:
    """Log each globally duplicate test display name. Never raises."""
    source = str(config_source) if config_source is not None else None
    for duplicate in find_duplicate_test_display_names(config):
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "issue": "duplicate_test_display_name",
            "test_name": duplicate.test_name,
            "occurrences": [
                {
                    "bundle_key": o.bundle_key,
                    "bundle_display_name": o.bundle_display_name,
                }
                for o in duplicate.occurrences
            ],
        }
        if source is not None:
            record["config_source"] = source
        log_startup_config_warning(record)
