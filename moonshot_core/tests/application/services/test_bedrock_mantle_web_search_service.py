"""Tests for Bedrock Mantle web search completion service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIStatusError

from application.services.bedrock_mantle_web_search_service import (
    BedrockWebSearchError,
    extract_citations_from_response_payload,
    run_web_search_completion,
)
@pytest.mark.asyncio
async def test_run_web_search_completion_returns_text_and_citations():
    mock_response = MagicMock()
    mock_response.output_text = "Answer with source"
    mock_response.model_dump.return_value = {
        "output_text": "Answer with source",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": "Answer with source",
                        "annotations": [
                            {
                                "type": "url_citation",
                                "url": "https://example.com/doc",
                                "title": "Example",
                            }
                        ],
                    }
                ],
            }
        ],
    }

    mock_client = MagicMock()
    mock_client.responses.create = AsyncMock(return_value=mock_response)

    result = await run_web_search_completion(
        prompt="What is new?",
        region="us-east-1",
        model_id="openai.gpt-5.5",
        api_key="test-key",
        client_factory=lambda: mock_client,
    )

    assert result.text == "Answer with source"
    assert len(result.citations) == 1
    assert result.citations[0].url == "https://example.com/doc"
    mock_client.responses.create.assert_awaited_once()
    call_kwargs = mock_client.responses.create.await_args.kwargs
    assert call_kwargs["tools"] == [
        {"type": "web_search", "external_web_access": False}
    ]


@pytest.mark.asyncio
async def test_run_web_search_completion_maps_auth_error():
    mock_client = MagicMock()
    mock_client.responses.create = AsyncMock(
        side_effect=APIStatusError(
            "Unauthorized",
            response=MagicMock(status_code=401),
            body=None,
        )
    )

    with patch(
        "application.services.bedrock_mantle_web_search_service.dump_api_failure"
    ) as dump_mock:
        with pytest.raises(BedrockWebSearchError) as exc_info:
            await run_web_search_completion(
                prompt="hi",
                region="us-east-1",
                model_id="openai.gpt-5.5",
                api_key="bad-key",
                client_factory=lambda: mock_client,
            )
    assert exc_info.value.error_code == "AUTH_FAILED"
    dump_mock.assert_called_once()
    call_kwargs = dump_mock.call_args.kwargs
    assert call_kwargs["adapter_name"] == "BedrockMantleWebSearchAdapter"
    assert call_kwargs["request"]["model"] == "openai.gpt-5.5"
    assert call_kwargs["request"]["tools"] == [
        {"type": "web_search", "external_web_access": False}
    ]
    assert call_kwargs["extra"]["base_url"].endswith("/openai/v1")


def test_extract_citations_from_dict_payload():
    payload = {
        "output": [
            {
                "content": [
                    {
                        "annotations": [
                            {"type": "url_citation", "url": "https://a.test", "title": "A"}
                        ]
                    }
                ]
            }
        ]
    }
    citations = extract_citations_from_response_payload(payload)
    assert len(citations) == 1
    assert citations[0].url == "https://a.test"

