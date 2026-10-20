"""Tests for api_failure_dump helper."""

import json
import logging
from io import StringIO
from pathlib import Path

import pytest

from adapters.connector import api_failure_dump as dump_mod
from adapters.connector.api_failure_dump import (
    API_FAILURE_LOGGER_NAME,
    MAX_BODY_CHARS,
    dump_api_failure,
    extract_error_details,
    redact_for_dump,
    resolve_api_failure_log_path,
)


def _close_dedicated_logger_handlers() -> None:
    dedicated = logging.getLogger(API_FAILURE_LOGGER_NAME)
    for handler in dedicated.handlers[:]:
        dedicated.removeHandler(handler)
        handler.close()


@pytest.fixture(autouse=True)
def isolate_api_failure_dump(monkeypatch):
    """Reset the dedicated file logger and path env vars between tests."""
    monkeypatch.delenv("MS_API_FAILURE_LOG_PATH", raising=False)
    monkeypatch.delenv("MOONSHOT_BENCHMARK_RESULTS_DIR", raising=False)
    _close_dedicated_logger_handlers()
    yield
    _close_dedicated_logger_handlers()


def test_redact_for_dump_scrubs_secret_keys():
    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "api_key": "sk-secret",
        "headers": {
            "Authorization": "Bearer sk-secret",
            "X-API-Key": "secret",
            "Content-Type": "application/json",
        },
        "aws_secret_access_key": "aws-secret",
    }

    redacted = redact_for_dump(payload)

    assert redacted["messages"][0]["content"] == "hello"
    assert redacted["api_key"] == "***REDACTED***"
    assert redacted["headers"]["Authorization"] == "***REDACTED***"
    assert redacted["headers"]["X-API-Key"] == "***REDACTED***"
    assert redacted["headers"]["Content-Type"] == "application/json"
    assert redacted["aws_secret_access_key"] == "***REDACTED***"


def test_extract_error_details_reads_status_and_body():
    class FakeError(Exception):
        def __init__(self):
            super().__init__("bad request")
            self.status_code = 400
            self.body = {"error": {"message": "invalid"}}

    details = extract_error_details(FakeError())

    assert details["exception_type"] == "FakeError"
    assert details["status_code"] == 400
    assert details["body"] == {"error": {"message": "invalid"}}


def test_dump_api_failure_writes_redacted_json(tmp_path: Path, monkeypatch):
    log_path = tmp_path / "api_failures.log"
    monkeypatch.setenv("MS_API_FAILURE_LOG_PATH", str(log_path))

    class FakeError(Exception):
        def __init__(self):
            super().__init__("rejected")
            self.status_code = 429
            self.body = {"error": "rate_limit"}

    dump_api_failure(
        adapter_name="OpenAIAdapter",
        request={"model": "gpt-4", "api_key": "sk-live", "messages": [{"role": "user", "content": "hi"}]},
        error=FakeError(),
        model="gpt-4",
    )

    text = log_path.read_text(encoding="utf-8")
    assert "OpenAIAdapter" in text
    assert "sk-live" not in text
    assert "***REDACTED***" in text
    assert '"content": "hi"' in text
    record = json.loads(text.split("=" * 72, 1)[1].strip())
    assert record["adapter"] == "OpenAIAdapter"
    assert record["model"] == "gpt-4"
    assert record["error"]["status_code"] == 429


def test_dump_api_failure_truncates_large_strings(tmp_path: Path, monkeypatch):
    log_path = tmp_path / "api_failures.log"
    monkeypatch.setenv("MS_API_FAILURE_LOG_PATH", str(log_path))

    huge = "x" * (MAX_BODY_CHARS + 500)
    dump_api_failure(
        adapter_name="CustomApiConnectorAdapter",
        request={"body": huge},
        error=RuntimeError("boom"),
    )

    text = log_path.read_text(encoding="utf-8")
    assert "[truncated" in text
    assert huge not in text


def test_dump_api_failure_never_raises(monkeypatch):
    def _boom():
        raise OSError("disk full")

    monkeypatch.setattr(dump_mod, "resolve_api_failure_log_path", _boom)
    # Must not raise
    dump_api_failure(
        adapter_name="OpenAIAdapter",
        request={"messages": []},
        error=RuntimeError("api failed"),
    )


def test_resolve_api_failure_log_path(tmp_path: Path, monkeypatch):
    target = tmp_path / "nested" / "failures"
    monkeypatch.setenv("MS_API_FAILURE_LOG_PATH", str(target))
    resolved = resolve_api_failure_log_path()
    assert resolved.suffix == ".log"
    assert resolved.parent.exists()


def test_resolve_api_failure_log_path_derives_from_results_dir(
    tmp_path: Path, monkeypatch
):
    results_dir = tmp_path / "results"
    monkeypatch.setenv("MOONSHOT_BENCHMARK_RESULTS_DIR", str(results_dir))

    resolved = resolve_api_failure_log_path()

    assert resolved == (results_dir / "api_failures.log").resolve()
    assert resolved.parent.exists()


def test_resolve_api_failure_log_path_explicit_override_wins(
    tmp_path: Path, monkeypatch
):
    explicit = tmp_path / "explicit.log"
    monkeypatch.setenv("MS_API_FAILURE_LOG_PATH", str(explicit))
    monkeypatch.setenv("MOONSHOT_BENCHMARK_RESULTS_DIR", str(tmp_path / "results"))

    assert resolve_api_failure_log_path() == explicit.resolve()


def test_resolve_api_failure_log_path_defaults_to_data_results(monkeypatch):
    resolved = resolve_api_failure_log_path()

    assert resolved == Path("data/results/api_failures.log").resolve()


def test_dump_api_failure_writes_to_derived_results_dir_path(
    tmp_path: Path, monkeypatch
):
    results_dir = tmp_path / "results"
    monkeypatch.setenv("MOONSHOT_BENCHMARK_RESULTS_DIR", str(results_dir))

    dump_api_failure(adapter_name="OpenAIAdapter", error=RuntimeError("boom"))

    text = (results_dir / "api_failures.log").read_text(encoding="utf-8")
    assert "OpenAIAdapter" in text


def test_dump_api_failure_uses_dedicated_logger_only(tmp_path: Path, monkeypatch):
    log_path = tmp_path / "api_failures.log"
    monkeypatch.setenv("MS_API_FAILURE_LOG_PATH", str(log_path))
    # Dedicated dumps must survive a restrictive main-log level.
    monkeypatch.setenv("MS_LOG_LEVEL", "WARNING")

    root_stream = StringIO()
    root_handler = logging.StreamHandler(root_stream)
    root = logging.getLogger()
    root.addHandler(root_handler)
    try:
        dump_api_failure(adapter_name="DedicatedAdapter", error=RuntimeError("boom"))
        dump_api_failure(adapter_name="DedicatedAdapter", error=RuntimeError("boom2"))
    finally:
        root.removeHandler(root_handler)
        root_handler.close()

    dedicated = logging.getLogger(API_FAILURE_LOGGER_NAME)
    assert dedicated.propagate is False
    assert len(dedicated.handlers) == 1
    assert isinstance(dedicated.handlers[0], logging.FileHandler)
    assert Path(dedicated.handlers[0].baseFilename) == log_path.resolve()

    text = log_path.read_text(encoding="utf-8")
    assert text.count("=" * 72) == 2
    assert "DedicatedAdapter" in text
    assert "DedicatedAdapter" not in root_stream.getvalue()


def test_dump_api_failure_repoints_handler_when_path_changes(
    tmp_path: Path, monkeypatch
):
    first = tmp_path / "first.log"
    second = tmp_path / "second.log"

    monkeypatch.setenv("MS_API_FAILURE_LOG_PATH", str(first))
    dump_api_failure(adapter_name="FirstAdapter", error=RuntimeError("one"))

    monkeypatch.setenv("MS_API_FAILURE_LOG_PATH", str(second))
    dump_api_failure(adapter_name="SecondAdapter", error=RuntimeError("two"))

    dedicated = logging.getLogger(API_FAILURE_LOGGER_NAME)
    assert len(dedicated.handlers) == 1
    assert Path(dedicated.handlers[0].baseFilename) == second.resolve()
    assert "SecondAdapter" not in first.read_text(encoding="utf-8")
    assert "SecondAdapter" in second.read_text(encoding="utf-8")
