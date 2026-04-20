"""Strip connector-level keys from kwargs merged for chat completion SDK calls.

These keys come from provider defaults / DB–YAML merges on ``ConnectorEntity.params``
and must not be forwarded into ``chat.completions.create``-style APIs.
"""

from __future__ import annotations

# Connector / merge artifacts (not chat completion parameters).
# Also SDK client hook names we do not inject from merged operator params.
DEFAULT_STRIP_KEYS_FROM_CHAT_COMPLETION: frozenset[str] = frozenset(
    {
        "api_type",
        "base_url",
        "extra_headers",
        "extra_query",
        "extra_body",
        "timeout",
    }
)


def strip_connector_keys_for_chat_completion(
    params: dict,
    *,
    extra_keys: frozenset[str] | None = None,
) -> dict:
    """Return a new dict omitting known connector keys and optional ``extra_keys``."""
    skip = DEFAULT_STRIP_KEYS_FROM_CHAT_COMPLETION
    if extra_keys:
        skip = skip | extra_keys
    return {k: v for k, v in params.items() if k not in skip}
