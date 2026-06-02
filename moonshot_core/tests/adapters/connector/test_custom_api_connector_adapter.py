import json

import pytest

from adapters.connector.custom_api_connector_adapter import CustomApiConnectorAdapter
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

    def test_build_request_body_honors_pre_post_and_system_prompts(self):
        adapter = _configured_adapter(
            connector_pre_prompt="PRE:",
            connector_post_prompt=":POST",
            system_prompt="SYS",
        )
        body = adapter._build_request_body("mid")

        assert body["messages"] == [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "PRE:mid:POST"},
        ]

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
            "messages": [{"role": "user", "content": "placeholder"}],
        }
        adapter = _configured_adapter(api_body=json.dumps(template))
        body = adapter._build_request_body("live prompt")

        assert body["model"] == "custom-model"
        assert body["max_tokens"] == 64
        assert body["messages"][-1]["content"] == "live prompt"
