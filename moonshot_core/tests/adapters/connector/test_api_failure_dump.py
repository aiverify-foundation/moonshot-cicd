"""Tests for api_failure_dump helper."""

import json
from pathlib import Path

from adapters.connector import api_failure_dump as dump_mod
from adapters.connector.api_failure_dump import (
    MAX_BODY_CHARS,
    dump_api_failure,
    extract_error_details,
    redact_for_dump,
    resolve_api_failure_log_path,
)


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
