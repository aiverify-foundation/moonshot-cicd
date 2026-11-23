"""Tests for startup_config_warnings helper."""

import json
import logging
from pathlib import Path

import pytest

from application.services import startup_config_warnings as warnings_mod
from application.services.startup_config_warnings import (
    STARTUP_CONFIG_WARNINGS_LOGGER_NAME,
    find_duplicate_test_display_names,
    log_startup_config_warning,
    report_duplicate_test_display_names,
    resolve_startup_config_warnings_log_path,
)


def _close_dedicated_logger_handlers() -> None:
    dedicated = logging.getLogger(STARTUP_CONFIG_WARNINGS_LOGGER_NAME)
    for handler in dedicated.handlers[:]:
        dedicated.removeHandler(handler)
        handler.close()


@pytest.fixture(autouse=True)
def isolate_startup_config_warnings(monkeypatch):
    monkeypatch.delenv("MS_STARTUP_CONFIG_WARNINGS_LOG_PATH", raising=False)
    monkeypatch.delenv("MOONSHOT_BENCHMARK_RESULTS_DIR", raising=False)
    _close_dedicated_logger_handlers()
    yield
    _close_dedicated_logger_handlers()


def test_find_duplicate_test_display_names_global():
    config = {
        "bundle-a": {
            "name": "Bundle A",
            "tests": [
                {"name": "Shared Test", "dataset": "d1", "metric": {"name": "m"}},
            ],
        },
        "bundle-b": {
            "name": "Bundle B",
            "tests": [
                {"name": "Shared Test", "dataset": "d2", "metric": {"name": "m"}},
                {"name": "Unique", "dataset": "d2", "metric": {"name": "m"}},
            ],
        },
    }

    duplicates = find_duplicate_test_display_names(config)

    assert len(duplicates) == 1
    assert duplicates[0].test_name == "Shared Test"
    assert len(duplicates[0].occurrences) == 2
    keys = {o.bundle_key for o in duplicates[0].occurrences}
    assert keys == {"bundle-a", "bundle-b"}


def test_find_duplicate_test_display_names_same_bundle_twice():
    config = {
        "bundle-a": {
            "tests": [
                {"name": "Dup", "dataset": "d1", "metric": {"name": "m"}},
                {"name": "Dup", "dataset": "d2", "metric": {"name": "m"}},
            ],
        },
    }

    duplicates = find_duplicate_test_display_names(config)

    assert len(duplicates) == 1
    assert len(duplicates[0].occurrences) == 2


def test_find_duplicate_test_display_names_case_sensitive():
    config = {
        "a": {"tests": [{"name": "Test", "dataset": "d", "metric": {"name": "m"}}]},
        "b": {"tests": [{"name": "test", "dataset": "d", "metric": {"name": "m"}}]},
    }

    assert find_duplicate_test_display_names(config) == []


def test_resolve_startup_config_warnings_log_path_explicit(tmp_path: Path, monkeypatch):
    explicit = tmp_path / "custom_warnings.log"
    monkeypatch.setenv("MS_STARTUP_CONFIG_WARNINGS_LOG_PATH", str(explicit))

    assert resolve_startup_config_warnings_log_path() == explicit.resolve()


def test_resolve_startup_config_warnings_log_path_from_results_dir(
    tmp_path: Path, monkeypatch
):
    results_dir = tmp_path / "results"
    monkeypatch.setenv("MOONSHOT_BENCHMARK_RESULTS_DIR", str(results_dir))

    resolved = resolve_startup_config_warnings_log_path()

    assert resolved == (results_dir / "startup_config_warnings.log").resolve()


def test_log_startup_config_warning_appends_json(tmp_path: Path, monkeypatch):
    log_path = tmp_path / "startup_config_warnings.log"
    monkeypatch.setenv("MS_STARTUP_CONFIG_WARNINGS_LOG_PATH", str(log_path))

    log_startup_config_warning({"issue": "duplicate_test_display_name", "test_name": "X"})

    text = log_path.read_text(encoding="utf-8")
    assert "duplicate_test_display_name" in text
    assert json.loads(text.split("=" * 72 + "\n")[1].strip())["test_name"] == "X"


def test_report_duplicate_test_display_names_writes_one_block_per_name(
    tmp_path: Path, monkeypatch
):
    log_path = tmp_path / "warnings.log"
    monkeypatch.setenv("MS_STARTUP_CONFIG_WARNINGS_LOG_PATH", str(log_path))
    config = {
        "a": {"tests": [{"name": "D1", "dataset": "d", "metric": {"name": "m"}}]},
        "b": {"tests": [{"name": "D1", "dataset": "d", "metric": {"name": "m"}}]},
        "c": {"tests": [{"name": "D2", "dataset": "d", "metric": {"name": "m"}}]},
        "d": {"tests": [{"name": "D2", "dataset": "d", "metric": {"name": "m"}}]},
    }

    report_duplicate_test_display_names(config, "/fake/shared.yaml")

    assert log_path.read_text(encoding="utf-8").count("duplicate_test_display_name") == 2


def test_log_startup_config_warning_swallows_write_errors(monkeypatch):
    def _raise_os_error():
        raise OSError("disk full")

    monkeypatch.setattr(
        warnings_mod,
        "resolve_startup_config_warnings_log_path",
        _raise_os_error,
    )

    log_startup_config_warning({"issue": "x"})
