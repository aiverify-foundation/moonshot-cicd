"""Append redacted API request/response dumps on connector failures."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domain.services.ga_results_formatter import SECRET_PARAM_KEYS
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

DEFAULT_API_FAILURE_LOG_PATH = "data/results/api_failures.log"
MAX_BODY_CHARS = 32_768
_REDACTED = "***REDACTED***"

# Header / param keys that must never appear in dumps (case-insensitive).
_SECRET_HEADER_KEYS = frozenset(
    {
        "authorization",
        "x-api-key",
        "api-key",
        "api_key",
        "aws_secret_access_key",
        "aws_access_key_id",
        "x-amz-security-token",
        "proxy-authorization",
        "cookie",
        "set-cookie",
    }
) | SECRET_PARAM_KEYS


def resolve_api_failure_log_path() -> Path:
    """Resolve dump file path from MS_API_FAILURE_LOG_PATH (default under data/results/)."""
    log_path = os.getenv("MS_API_FAILURE_LOG_PATH", DEFAULT_API_FAILURE_LOG_PATH)
    file_path = Path(log_path)
    if file_path.suffix == "":
        file_path = file_path.with_suffix(".log")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path.resolve()


def _is_secret_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    normalized = key.lower().replace("-", "_")
    if key.lower() in _SECRET_HEADER_KEYS or normalized in _SECRET_HEADER_KEYS:
        return True
    # Also match hyphenated header forms against underscore secret keys.
    return key.lower() in {k.replace("_", "-") for k in _SECRET_HEADER_KEYS}


def redact_for_dump(value: Any) -> Any:
    """Recursively redact secret-like keys; leave other values intact."""
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            if _is_secret_key(key):
                out[key] = _REDACTED
            else:
                out[key] = redact_for_dump(item)
        return out
    if isinstance(value, list):
        return [redact_for_dump(item) for item in value]
    if isinstance(value, tuple):
        return [redact_for_dump(item) for item in value]
    return value


def _truncate(text: str, max_chars: int = MAX_BODY_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    omitted = len(text) - max_chars
    return f"{text[:max_chars]}... [truncated {omitted} chars]"


def _safe_serialize(value: Any) -> Any:
    """Convert value to JSON-serializable form, truncating large strings."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _truncate(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            return _truncate(value.decode("utf-8", errors="replace"))
        except Exception:
            return _REDACTED
    if isinstance(value, dict):
        return {str(k): _safe_serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_serialize(item) for item in value]
    # Prefer model_dump / dict when available (Pydantic / SDK objects).
    for attr in ("model_dump", "dict", "to_dict"):
        method = getattr(value, attr, None)
        if callable(method):
            try:
                return _safe_serialize(method())
            except Exception:
                pass
    try:
        return _truncate(str(value))
    except Exception:
        return f"<unserializable {type(value).__name__}>"


def extract_error_details(error: BaseException) -> dict[str, Any]:
    """Pull status_code / body / response from common SDK and HTTP exceptions."""
    details: dict[str, Any] = {
        "exception_type": type(error).__name__,
        "exception_message": str(error),
    }

    status_code = getattr(error, "status_code", None)
    if status_code is None:
        status_code = getattr(error, "status", None)
    if status_code is not None:
        details["status_code"] = status_code

    body = getattr(error, "body", None)
    if body is not None:
        details["body"] = _safe_serialize(body)

    response = getattr(error, "response", None)
    if response is not None:
        response_payload: dict[str, Any] = {"repr": _truncate(str(response))}
        resp_status = getattr(response, "status_code", None) or getattr(
            response, "status", None
        )
        if resp_status is not None:
            response_payload["status_code"] = resp_status
            if "status_code" not in details:
                details["status_code"] = resp_status
        for attr in ("text", "content"):
            raw = getattr(response, attr, None)
            if raw is None:
                continue
            if callable(raw):
                continue
            response_payload[attr] = _safe_serialize(raw)
            break
        details["response"] = response_payload

    return details


def dump_api_failure(
    *,
    adapter_name: str,
    request: Any = None,
    error: BaseException | None = None,
    model: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Append a redacted JSON dump of a failed API call.

    Never raises — dump failures are logged and swallowed so the original
    connector exception remains the one that propagates.
    """
    try:
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "adapter": adapter_name,
        }
        if model is not None:
            record["model"] = model
        if request is not None:
            record["request"] = _safe_serialize(redact_for_dump(request))
        if error is not None:
            record["error"] = extract_error_details(error)
        if extra:
            record["extra"] = _safe_serialize(redact_for_dump(extra))

        path = resolve_api_failure_log_path()
        block = (
            "\n"
            + "=" * 72
            + "\n"
            + json.dumps(record, indent=2, ensure_ascii=False, default=str)
            + "\n"
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(block)
    except Exception as dump_error:
        logger.warning(
            "[api_failure_dump] Failed to write API failure dump for %s: %s",
            adapter_name,
            dump_error,
        )
