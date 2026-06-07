import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adapters.connector.custom_api_connector_adapter import CustomApiConnectorAdapter

CONNECTION_TEST_PROMPT = "Hase the connection passed ? "
from domain.entities.connector_entity import ConnectorEntity


def _configured_adapter(**params: str) -> CustomApiConnectorAdapter:
    adapter = CustomApiConnectorAdapter()
    adapter.configure(
        ConnectorEntity(
            connector_adapter="custom_api_connector_adapter",
            model="",
            params={
                "api_type": "POST",
                "api_url": "https://api.together.xyz/v1/chat/completions",
                "api_body": params.get("api_body", CustomApiConnectorAdapter.DEFAULT_CONFIG_PAIRS["api_body"]),
                **{k: v for k, v in params.items() if k != "api_body"},
            },
            connector_pre_prompt=params.get("connector_pre_prompt", ""),
            connector_post_prompt=params.get("connector_post_prompt", ""),
            system_prompt=params.get("system_prompt", ""),
        )
    )
    return adapter


class TestCustomApiConnectorAdapter:
    def test_build_request_body_injects_prompt_into_messages(self):
        adapter = _configured_adapter()
        body = adapter._build_request_body("benchmark prompt text")

        assert body["model"] == "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        assert body["messages"] == [
            {"role": "user", "content": "benchmark prompt text"},
        ]

    def test_build_request_body_honors_pre_post_prompts(self):
        adapter = _configured_adapter(
            api_body=json.dumps(
                {"messages": [{"role": "user", "content": "{{prompt}}"}]}
            ),
            connector_pre_prompt="PRE:",
            connector_post_prompt=":POST",
        )
        body = adapter._build_request_body("mid")

        assert body["messages"] == [
            {"role": "user", "content": "PRE:mid:POST"},
        ]

    def test_configure_rejects_missing_prompt_placeholder(self):
        adapter = CustomApiConnectorAdapter()
        with pytest.raises(ValueError, match="api_body must include the '{{prompt}}' placeholder"):
            adapter.configure(
                ConnectorEntity(
                    connector_adapter="custom_api_connector_adapter",
                    model="",
                    params={
                        "api_body": json.dumps(
                            {"messages": [{"role": "user", "content": ""}]}
                        ),
                    },
                )
            )

    def test_configure_rejects_invalid_api_body_json(self):
        adapter = CustomApiConnectorAdapter()
        with pytest.raises(ValueError, match="Invalid api_body JSON"):
            adapter.configure(
                ConnectorEntity(
                    connector_adapter="custom_api_connector_adapter",
                    model="",
                    params={"api_body": "not-json"},
                )
            )

    def test_configure_parses_custom_template(self):
        template = {
            "model": "custom-model",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "{{prompt}}"}],
        }
        adapter = _configured_adapter(api_body=json.dumps(template))
        body = adapter._build_request_body("live prompt")

        assert body["model"] == "custom-model"
        assert body["max_tokens"] == 64
        assert body["messages"][-1]["content"] == "live prompt"

    @pytest.mark.parametrize(
        ("scheme", "custom_header", "expected"),
        [
            ("bearer", "", ("Authorization", "Bearer sk-test")),
            ("authorization_api_key", "", ("Authorization", "ApiKey sk-test")),
            ("x_api_key", "", ("X-API-Key", "sk-test")),
            ("x_api_key_lower", "", ("x-api-key", "sk-test")),
            ("custom", "X-Auth-Token", ("X-Auth-Token", "sk-test")),
        ],
    )
    def test_build_auth_header(self, scheme, custom_header, expected):
        adapter = _configured_adapter(
            api_key="sk-test",
            api_key_auth_scheme=scheme,
            api_key_auth_custom_header=custom_header,
        )
        assert adapter._build_auth_header() == expected

    def test_inject_prompt_replaces_nested_placeholders(self):
        template = {
            "input": "{{prompt}}",
            "messages": [{"role": "user", "content": "prefix {{prompt}} suffix"}],
        }
        adapter = _configured_adapter(api_body=json.dumps(template))
        body = adapter._build_request_body("hello")

        assert body["input"] == "hello"
        assert body["messages"][0]["content"] == "prefix hello suffix"

    def test_build_auth_header_returns_none_without_secret(self, monkeypatch):
        monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
        adapter = _configured_adapter(api_key="")
        assert adapter._build_auth_header() is None

    def test_build_auth_header_custom_without_header_name(self):
        adapter = _configured_adapter(api_key="sk-test", api_key_auth_scheme="custom")
        assert adapter._build_auth_header() is None

    def test_build_request_headers_merges_custom_headers_and_auth(self):
        adapter = _configured_adapter(
            api_key="sk-test",
            headers=json.dumps({"Accept": "application/json", "X-Custom": "value"}),
        )
        headers = adapter._build_request_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["X-Custom"] == "value"
        assert headers["Authorization"] == "Bearer sk-test"

    @pytest.mark.asyncio
    async def test_probe_returns_raw_status_and_body(self):
        adapter = _configured_adapter(
            api_key="sk-test",
            api_url="https://api.example.com/v1/chat",
            headers=json.dumps({"X-Test": "1"}),
        )

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"choices":[]}')

        mock_request_ctx = MagicMock()
        mock_request_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_request_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=mock_request_ctx)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "adapters.connector.custom_api_connector_adapter.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            status, body = await adapter.probe(CONNECTION_TEST_PROMPT)

        assert status == 200
        assert body == '{"choices":[]}'
        request_kwargs = mock_session.request.call_args.kwargs
        assert request_kwargs["headers"]["Authorization"] == "Bearer sk-test"
        assert request_kwargs["headers"]["X-Test"] == "1"
        assert (
            request_kwargs["json"]["messages"][0]["content"] == CONNECTION_TEST_PROMPT
        )

    def test_extract_response_value_default_path(self):
        adapter = _configured_adapter()
        payload = {
            "choices": [{"message": {"content": "hello from api"}}],
        }
        assert adapter._extract_response_value(payload) == "hello from api"

    def test_extract_response_value_custom_path(self):
        adapter = _configured_adapter(response_path="result.text")
        payload = {"result": {"text": "custom reply"}}
        assert adapter._extract_response_value(payload) == "custom reply"

    def test_configure_rejects_empty_response_path(self):
        adapter = CustomApiConnectorAdapter()
        with pytest.raises(ValueError, match="response_path must be a non-empty"):
            adapter.configure(
                ConnectorEntity(
                    connector_adapter="custom_api_connector_adapter",
                    model="",
                    params={
                        "api_body": CustomApiConnectorAdapter.DEFAULT_CONFIG_PAIRS["api_body"],
                        "response_path": "   ",
                    },
                )
            )

    def test_configure_rejects_invalid_response_path(self):
        adapter = CustomApiConnectorAdapter()
        with pytest.raises(ValueError, match="Invalid response_path JSONPath"):
            adapter.configure(
                ConnectorEntity(
                    connector_adapter="custom_api_connector_adapter",
                    model="",
                    params={
                        "api_body": CustomApiConnectorAdapter.DEFAULT_CONFIG_PAIRS["api_body"],
                        "response_path": "[invalid",
                    },
                )
            )

    def test_extract_response_value_path_not_found(self):
        adapter = _configured_adapter(response_path="missing.field")
        with pytest.raises(ValueError, match="No value found at response_path"):
            adapter._extract_response_value({"choices": []})

    @pytest.mark.asyncio
    async def test_get_response_uses_response_path(self):
        adapter = _configured_adapter(
            api_key="sk-test",
            response_path="output",
        )

        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={"output": "benchmark result"})

        mock_request_ctx = MagicMock()
        mock_request_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_request_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=mock_request_ctx)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "adapters.connector.custom_api_connector_adapter.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            result = await adapter.get_response("prompt")

        assert result.response == "benchmark result"
