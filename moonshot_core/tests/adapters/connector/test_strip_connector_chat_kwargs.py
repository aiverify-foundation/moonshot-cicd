"""Tests for strip_connector_keys_for_chat_completion and numeric coercion."""

from unittest.mock import patch

from adapters.connector.strip_connector_chat_kwargs import (
    coerce_numeric_string_chat_params,
    strip_connector_keys_for_chat_completion,
)


def test_strip_removes_known_connector_and_sdk_hook_keys():
    params = {
        "api_key": "sk-secret",
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
        "api_key",
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


def test_coerce_parses_string_floats_and_ints():
    params = {
        "temperature": "0.7",
        "top_p": "0.95",
        "frequency_penalty": "0",
        "presence_penalty": "-0.5",
        "max_tokens": "128",
        "max_completion_tokens": "256",
        "seed": "42",
        "n": "1",
        "top_logprobs": "5",
        "model": "gpt-4o-mini",
    }
    out = coerce_numeric_string_chat_params(params)
    assert out["temperature"] == 0.7
    assert out["top_p"] == 0.95
    assert out["frequency_penalty"] == 0.0
    assert out["presence_penalty"] == -0.5
    assert out["max_tokens"] == 128
    assert out["max_completion_tokens"] == 256
    assert out["seed"] == 42
    assert out["n"] == 1
    assert out["top_logprobs"] == 5
    assert out["model"] == "gpt-4o-mini"
    assert params["temperature"] == "0.7"


def test_coerce_leaves_non_string_numerics_unchanged():
    params = {"temperature": 0.2, "max_tokens": 100}
    assert coerce_numeric_string_chat_params(params) == params


def test_coerce_invalid_float_string_drops_key_and_warns():
    params = {"temperature": "not-a-number", "model": "x"}
    with patch(
        "adapters.connector.strip_connector_chat_kwargs._logger"
    ) as mock_logger:
        out = coerce_numeric_string_chat_params(params)
    assert "temperature" not in out
    assert out == {"model": "x"}
    mock_logger.warning.assert_called_once()


def test_coerce_invalid_int_string_drops_key_and_warns():
    params = {"max_tokens": "oops", "model": "x"}
    with patch(
        "adapters.connector.strip_connector_chat_kwargs._logger"
    ) as mock_logger:
        out = coerce_numeric_string_chat_params(params)
    assert "max_tokens" not in out
    assert out == {"model": "x"}
    mock_logger.warning.assert_called_once()


def test_strip_then_coerce_end_to_end():
    merged = {
        "api_type": "openai",
        "base_url": "https://api.openai.com/v1",
        "temperature": "0.2",
        "max_tokens": "512",
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "hi"}],
    }
    stripped = strip_connector_keys_for_chat_completion(merged)
    out = coerce_numeric_string_chat_params(stripped)
    assert out["temperature"] == 0.2
    assert out["max_tokens"] == 512
    assert "api_type" not in out
    assert "base_url" not in out
