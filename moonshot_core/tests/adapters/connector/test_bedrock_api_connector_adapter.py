import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adapters.connector.bedrock_api_connector_adapter import (
    DEFAULT_BEDROCK_MODEL,
    BedrockApiConnectorAdapter,
    _classify_bedrock_response_format,
    _detect_model_family,
    _extract_converse_assistant_text,
    _infer_bedrock_api_format_from_url,
    _parse_model_id_from_converse_url,
    _resolve_configured_model_id,
    _strip_inference_profile_prefix,
)
from domain.entities.connector_entity import ConnectorEntity


def _converse_payload(content: list) -> dict:
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": content,
            }
        }
    }


def _responses_payload(*, answer_text: str, model: str = "us.openai.gpt-6-astra") -> dict:
    return {
        "object": "response",
        "model": model,
        "status": "completed",
        "output": [
            {
                "type": "reasoning",
                "content": [],
                "encrypted_content": "rsn_redacted_blob",
                "id": "rs_test",
            },
            {
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {
                        "type": "output_text",
                        "text": answer_text,
                    }
                ],
                "id": "msg_test",
            },
        ],
    }


def _configured_adapter(*, model: str = "", **params: str) -> BedrockApiConnectorAdapter:
    adapter = BedrockApiConnectorAdapter()
    defaults = dict(BedrockApiConnectorAdapter.DEFAULT_CONFIG_PAIRS)
    merged = {**defaults, **params}
    adapter.configure(
        ConnectorEntity(
            connector_adapter="bedrock_api_connector_adapter",
            model=model,
            params=merged,
            connector_pre_prompt=params.get("connector_pre_prompt", ""),
            connector_post_prompt=params.get("connector_post_prompt", ""),
        )
    )
    return adapter


class TestBedrockApiConnectorAdapter:
    def test_default_config_pairs_use_converse_url_and_body(self):
        pairs = BedrockApiConnectorAdapter.DEFAULT_CONFIG_PAIRS
        assert pairs["api_type"] == "POST"
        assert "bedrock-runtime.us-east-1.amazonaws.com" in pairs["api_url"]
        assert "openai.gpt-oss-20b-1:0" in pairs["api_url"]
        assert pairs["api_url"].endswith("/converse")
        assert pairs["response_path"] == "output.message.content[0].text"
        body = json.loads(pairs["api_body"])
        assert body["messages"][0]["content"][0]["text"] == "{{prompt}}"

    def test_build_request_body_injects_prompt_into_converse_message(self):
        adapter = _configured_adapter()
        body = adapter._build_request_body("benchmark prompt")

        assert body["messages"] == [
            {"role": "user", "content": [{"text": "benchmark prompt"}]},
        ]

    def test_build_auth_header_uses_bearer_by_default(self):
        adapter = _configured_adapter(api_key="bedrock-key-test")
        assert adapter._build_auth_header() == ("Authorization", "Bearer bedrock-key-test")

    def test_build_auth_header_falls_back_to_bedrock_env(self, monkeypatch):
        monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "env-bedrock-key")
        adapter = BedrockApiConnectorAdapter()
        adapter.configure(
            ConnectorEntity(
                connector_adapter="bedrock_api_connector_adapter",
                model="",
                params=dict(BedrockApiConnectorAdapter.DEFAULT_CONFIG_PAIRS),
            )
        )
        assert adapter._build_auth_header() == (
            "Authorization",
            "Bearer env-bedrock-key",
        )

    @pytest.mark.asyncio
    async def test_get_response_extracts_converse_output_text(self):
        adapter = _configured_adapter(api_key="sk-test")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(
            return_value=_converse_payload([{"text": "Hello from Bedrock"}])
        )

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
            result = await adapter.get_response("ping")

        assert result.response == "Hello from Bedrock"
        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["url"] == BedrockApiConnectorAdapter.DEFAULT_CONFIG_PAIRS["api_url"]
        assert call_kwargs["headers"]["Authorization"] == "Bearer sk-test"

    def test_extract_response_value_single_text_block_non_reasoning(self):
        adapter = _configured_adapter()
        payload = _converse_payload([{"text": "Hello from Bedrock"}])
        assert adapter._extract_response_value(payload) == "Hello from Bedrock"

    def test_extract_response_value_anthropic_reasoning_plus_text(self):
        adapter = _configured_adapter(
            api_url=(
                "https://bedrock-runtime.us-east-1.amazonaws.com/model/"
                "us.anthropic.claude-3-7-sonnet-20250219-v1:0/converse"
            ),
        )
        payload = _converse_payload(
            [
                {
                    "reasoningContent": {
                        "reasoningText": {
                            "text": "Internal chain of thought must not leak.",
                            "signature": "EqgBCkYQARgCIkCy0Q",
                        }
                    }
                },
                {"text": "# Advantages of AWS Bedrock\n\nAWS Bedrock is ..."},
            ]
        )
        assert (
            adapter._extract_response_value(payload)
            == "# Advantages of AWS Bedrock\n\nAWS Bedrock is ..."
        )

    def test_extract_response_value_openai_gpt_oss_reasoning_plus_text(self):
        adapter = _configured_adapter()
        payload = _converse_payload(
            [
                {
                    "reasoningContent": {
                        "reasoningText": {
                            "text": "The user asks who I am. Respond politely.",
                        }
                    }
                },
                {"text": "I'm ChatGPT, running on AWS Bedrock."},
            ]
        )
        assert (
            adapter._extract_response_value(payload)
            == "I'm ChatGPT, running on AWS Bedrock."
        )

    def test_extract_response_value_anthropic_redacted_thinking_only(self):
        adapter = _configured_adapter(
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        )
        payload = _converse_payload(
            [
                {
                    "reasoningContent": {
                        "redactedContent": "c2VjcmV0LXRoaW5raW5nLWJsb2I=",
                    }
                },
            ]
        )
        with pytest.raises(ValueError, match="no text content blocks"):
            adapter._extract_response_value(payload)

    def test_extract_response_value_truncated_reasoning_only(self, caplog):
        adapter = _configured_adapter(model=DEFAULT_BEDROCK_MODEL)
        payload = _converse_payload(
            [
                {
                    "reasoningContent": {
                        "reasoningText": {
                            "text": "Still thinking but ran out of tokens...",
                        }
                    }
                },
            ]
        )
        with pytest.raises(ValueError, match=DEFAULT_BEDROCK_MODEL):
            adapter._extract_response_value(payload)
        assert "No text blocks in Converse response" in caplog.text

    def test_extract_response_value_concatenates_multiple_text_blocks(self):
        adapter = _configured_adapter()
        payload = _converse_payload(
            [
                {"text": "Part one. "},
                {
                    "reasoningContent": {
                        "reasoningText": {"text": "skip me"},
                    }
                },
                {"text": "Part two."},
            ]
        )
        assert adapter._extract_response_value(payload) == "Part one. Part two."

    def test_extract_response_value_ignores_custom_response_path_in_params(self):
        adapter = _configured_adapter(
            response_path="output.message.content[1].text",
        )
        payload = _converse_payload(
            [
                {
                    "reasoningContent": {
                        "reasoningText": {"text": "reasoning only"},
                    }
                },
                {"text": "Block-aware final answer."},
            ]
        )
        assert adapter._extract_response_value(payload) == "Block-aware final answer."

    def test_extract_response_value_openai_responses_api_gpt6_astra(self):
        adapter = _configured_adapter(
            api_url="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1/responses",
            api_body=json.dumps(
                {
                    "model": "us.openai.gpt-6-astra",
                    "input": "{{prompt}}",
                }
            ),
        )
        answer = "You can draft an NDA yourself for a Singapore startup."
        payload = _responses_payload(answer_text=answer)
        assert adapter._extract_response_value(payload) == answer
        assert _resolve_configured_model_id(adapter, payload) == "us.openai.gpt-6-astra"

    def test_extract_response_value_responses_api_uses_output_text_field(self):
        adapter = _configured_adapter(
            api_url="https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1/responses",
        )
        payload = {
            "object": "response",
            "model": "openai.gpt-5.4",
            "output_text": "Direct output_text shortcut.",
            "output": [],
        }
        assert adapter._extract_response_value(payload) == "Direct output_text shortcut."

    def test_extract_response_value_responses_reasoning_only_raises(self, caplog):
        adapter = _configured_adapter(
            api_url="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1/responses",
            api_body=json.dumps({"model": "us.openai.gpt-6-astra", "input": "{{prompt}}"}),
        )
        payload = {
            "object": "response",
            "model": "us.openai.gpt-6-astra",
            "output": [
                {
                    "type": "reasoning",
                    "content": [],
                    "encrypted_content": "rsn_only",
                }
            ],
        }
        with pytest.raises(ValueError, match="no output_text"):
            adapter._extract_response_value(payload)
        assert "No output_text in OpenAI Responses response" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_openai_gpt_oss_reasoning_model(self):
        adapter = _configured_adapter(api_key="sk-test")
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(
            return_value=_converse_payload(
                [
                    {
                        "reasoningContent": {
                            "reasoningText": {
                                "text": "Planning the reply.",
                            }
                        }
                    },
                    {"text": "Final visible reply."},
                ]
            )
        )

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
            result = await adapter.get_response("ping")

        assert result.response == "Final visible reply."


class TestBedrockModelIdHelpers:
    @pytest.mark.parametrize(
        ("model_id", "expected"),
        [
            ("openai.gpt-oss-20b-1:0", "openai"),
            ("us.openai.gpt-oss-120b-1:0", "openai"),
            ("global.anthropic.claude-sonnet-4-20250514-v1:0", "anthropic"),
            ("eu.anthropic.claude-3-7-sonnet-20250219-v1:0", "anthropic"),
            ("meta.llama3-70b-instruct-v1:0", "unknown"),
        ],
    )
    def test_detect_model_family(self, model_id: str, expected: str):
        assert _detect_model_family(model_id) == expected

    @pytest.mark.parametrize(
        ("model_id", "expected_stripped"),
        [
            ("us.openai.gpt-oss-20b-1:0", "openai.gpt-oss-20b-1:0"),
            ("global.us.anthropic.claude-3-5-sonnet-20241022-v2:0", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
        ],
    )
    def test_strip_inference_profile_prefix(self, model_id: str, expected_stripped: str):
        assert _strip_inference_profile_prefix(model_id) == expected_stripped

    def test_parse_model_id_from_converse_url(self):
        url = (
            "https://bedrock-runtime.us-west-2.amazonaws.com/model/"
            "openai.gpt-oss-20b-1:0/converse"
        )
        assert _parse_model_id_from_converse_url(url) == "openai.gpt-oss-20b-1:0"

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (
                "https://bedrock-runtime.us-east-1.amazonaws.com/model/foo/converse",
                "converse",
            ),
            (
                "https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1/responses",
                "responses",
            ),
            ("https://api.example.com/v1/chat/completions", None),
        ],
    )
    def test_infer_bedrock_api_format_from_url(self, url: str, expected: str | None):
        assert _infer_bedrock_api_format_from_url(url) == expected

    def test_classify_bedrock_response_format(self):
        assert _classify_bedrock_response_format(_converse_payload([{"text": "hi"}])) == "converse"
        assert (
            _classify_bedrock_response_format(_responses_payload(answer_text="hi"))
            == "responses"
        )

    def test_resolve_model_id_from_responses_request_body(self):
        adapter = _configured_adapter(
            api_url="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1/responses",
            api_body=json.dumps({"model": "us.openai.gpt-6-astra", "input": "{{prompt}}"}),
        )
        assert _resolve_configured_model_id(adapter) == "us.openai.gpt-6-astra"

    def test_extract_converse_assistant_text_malformed_content_shape(self):
        with pytest.raises(ValueError, match="missing output.message.content"):
            _extract_converse_assistant_text({"output": {"message": {}}}, "test-model")

        with pytest.raises(ValueError, match="expected a list"):
            _extract_converse_assistant_text(
                {"output": {"message": {"content": "not-a-list"}}},
                "test-model",
            )
