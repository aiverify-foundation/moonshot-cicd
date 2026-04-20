"""Tests for strip_connector_keys_for_chat_completion."""

from adapters.connector.strip_connector_chat_kwargs import (
    strip_connector_keys_for_chat_completion,
)


def test_strip_removes_known_connector_and_sdk_hook_keys():
    params = {
        "api_type": "openai",
        "base_url": "https://example.com",
        "extra_headers": {},
        "extra_query": {},
        "extra_body": {},
        "timeout": 30,
        "temperature": 0.5,
        "model": "gpt-4o-mini",
    }
    out = strip_connector_keys_for_chat_completion(params)
    assert out == {"temperature": 0.5, "model": "gpt-4o-mini"}
    assert params.keys() == {
        "api_type",
        "base_url",
        "extra_headers",
        "extra_query",
        "extra_body",
        "timeout",
        "temperature",
        "model",
    }


def test_strip_preserves_normal_completion_params():
    params = {"temperature": 0.2, "max_tokens": 100, "top_p": 0.9}
    assert strip_connector_keys_for_chat_completion(params) == params


def test_strip_extra_keys_union():
    custom = frozenset({"legacy_key"})
    params = {"legacy_key": 1, "temperature": 0.1}
    out = strip_connector_keys_for_chat_completion(params, extra_keys=custom)
    assert out == {"temperature": 0.1}
