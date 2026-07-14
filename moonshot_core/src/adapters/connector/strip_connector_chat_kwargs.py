"""Strip connector-level keys from kwargs merged for chat completion SDK calls.

These keys come from provider defaults / DB–YAML merges on ``ConnectorEntity.params``
and must not be forwarded into ``chat.completions.create``-style APIs.

Also coerces allowlisted numeric parameters from strings (relational DB stores values
as text) to ``float`` / ``int`` before SDK calls.
"""

from __future__ import annotations

from domain.services.logger import configure_logger

_logger = configure_logger(__name__)

# Connector / merge artifacts (not chat completion parameters).
# Also SDK client hook names we do not inject from merged operator params.
DEFAULT_STRIP_KEYS_FROM_CHAT_COMPLETION: frozenset[str] = frozenset(
    {
        "api_key",
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


# OpenAI-compatible chat completion scalar params that must be numeric for the HTTP API.
# Only these keys are coerced from str; all other values are left unchanged.
CHAT_COMPLETION_FLOAT_STRING_KEYS: frozenset[str] = frozenset(
    {
        "temperature",
        "top_p",
        "frequency_penalty",
        "presence_penalty",
    }
)
CHAT_COMPLETION_INT_STRING_KEYS: frozenset[str] = frozenset(
    {
        "max_tokens",
        "max_completion_tokens",
        "seed",
        "n",
        "top_logprobs",
    }
)


def coerce_numeric_string_chat_params(params: dict) -> dict:
    """Return a shallow copy with allowlisted numeric fields parsed from strings.

    Relational ``llm_provider_model_config_parameters.value`` and some YAML configs
    supply numbers as strings. The OpenAI / Together SDKs expect real ``float`` /
    ``int`` values for these keys.

    Non-string values are unchanged. For an allowlisted key whose value is a string
    that does not parse as a number, the key is **dropped** from the result and a
    warning is logged (avoids sending invalid types to the API).

    Call after :func:`strip_connector_keys_for_chat_completion` so connector-only
    string keys are not considered here.
    """
    out = dict(params)
    for key in CHAT_COMPLETION_FLOAT_STRING_KEYS:
        if key not in out:
            continue
        val = out[key]
        if isinstance(val, str):
            try:
                out[key] = float(val.strip())
            except ValueError:
                _logger.warning(
                    "Dropping chat completion param %r: not a valid float (%r)",
                    key,
                    val,
                )
                del out[key]
    for key in CHAT_COMPLETION_INT_STRING_KEYS:
        if key not in out:
            continue
        val = out[key]
        if isinstance(val, str):
            try:
                out[key] = int(float(val.strip()))
            except ValueError:
                _logger.warning(
                    "Dropping chat completion param %r: not a valid int (%r)",
                    key,
                    val,
                )
                del out[key]
    return out
