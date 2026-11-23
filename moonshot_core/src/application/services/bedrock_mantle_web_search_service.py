"""Bedrock Mantle OpenAI Responses API with web_search tool."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from openai import APIStatusError, AsyncOpenAI

from adapters.connector.api_failure_dump import dump_api_failure
from domain.services.bedrock_mantle_web_search_constants import (
    is_allowed_model_id,
    is_allowed_region,
)
from domain.services.logger import get_logger

TEST_CONNECTION_PROMPT = "Reply with exactly: ok"
ADAPTER_NAME_FOR_DUMP = "BedrockMantleWebSearchAdapter"

logger = get_logger(__name__)


class BedrockWebSearchError(Exception):
    """Base error for Bedrock web search operations."""

    def __init__(self, message: str, *, error_code: str) -> None:
        super().__init__(message)
        self.error_code = error_code


@dataclass(frozen=True)
class WebSearchCitation:
    url: str
    title: str | None = None


@dataclass(frozen=True)
class WebSearchCompletionResult:
    text: str
    citations: list[WebSearchCitation]


def mantle_base_url(region: str) -> str:
    """OpenAI-compatible Responses API path (required for ``web_search`` tools)."""
    return f"https://bedrock-mantle.{region.strip()}.api.aws/openai/v1"


def default_web_search_tools(*, external_web_access: bool = False) -> list[dict[str, Any]]:
    """
    Bedrock server-side web search tool definition.

    ``external_web_access=False`` keeps fetch within AWS index/cache (recommended
    for Bedrock API keys without ``bedrock-websearch:ExternalWebAccess`` IAM).
    """
    return [{"type": "web_search", "external_web_access": external_web_access}]


def extract_citations_from_response_payload(payload: Any) -> list[WebSearchCitation]:
    """Collect URL citations from Responses API output annotations."""
    citations: list[WebSearchCitation] = []
    seen: set[str] = set()

    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif isinstance(payload, dict):
        data = payload
    else:
        return citations

    output = data.get("output")
    if not isinstance(output, list):
        return citations

    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            annotations = part.get("annotations")
            if not isinstance(annotations, list):
                continue
            for ann in annotations:
                if not isinstance(ann, dict):
                    continue
                ann_type = ann.get("type")
                url = ann.get("url")
                if ann_type == "url_citation" and isinstance(url, str) and url.strip():
                    normalized = url.strip()
                    if normalized not in seen:
                        seen.add(normalized)
                        title_val = ann.get("title")
                        title = str(title_val) if isinstance(title_val, str) else None
                        citations.append(WebSearchCitation(url=normalized, title=title))

    return citations


def _extract_output_text(payload: Any) -> str:
    if hasattr(payload, "output_text"):
        text = getattr(payload, "output_text", None)
        if isinstance(text, str) and text:
            return text
    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif isinstance(payload, dict):
        data = payload
    else:
        raise BedrockWebSearchError(
            "Unexpected response shape from Bedrock Mantle",
            error_code="WEB_SEARCH_NOT_SUPPORTED",
        )
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text
    output = data.get("output")
    if not isinstance(output, list):
        raise BedrockWebSearchError(
            "Model response has no output_text",
            error_code="WEB_SEARCH_NOT_SUPPORTED",
        )
    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") == "output_text":
                text_val = part.get("text")
                if isinstance(text_val, str):
                    parts.append(text_val)
    if not parts:
        raise BedrockWebSearchError(
            "Model response has no output_text",
            error_code="WEB_SEARCH_NOT_SUPPORTED",
        )
    return "".join(parts)


def validate_region_and_model(region: str, model_id: str) -> None:
    if not is_allowed_region(region):
        raise BedrockWebSearchError(
            f"Region {region!r} is not supported",
            error_code="INVALID_REGION",
        )
    if not is_allowed_model_id(model_id):
        raise BedrockWebSearchError(
            f"Model {model_id!r} is not supported",
            error_code="MODEL_NOT_SUPPORTED",
        )


def _map_api_error(exc: APIStatusError) -> BedrockWebSearchError:
    status = exc.status_code
    if status in (401, 403):
        return BedrockWebSearchError(
            "Authentication failed for Bedrock Mantle",
            error_code="AUTH_FAILED",
        )
    if status == 400:
        return BedrockWebSearchError(
            "Bedrock Mantle rejected the request (check region and model)",
            error_code="VALIDATION_ERROR",
        )
    return BedrockWebSearchError(
        "Bedrock Mantle request failed",
        error_code="VALIDATION_ERROR",
    )


AsyncOpenAIClientFactory = Callable[[], AsyncOpenAI]


async def run_web_search_completion(
    *,
    prompt: str,
    region: str,
    model_id: str,
    api_key: str,
    client_factory: AsyncOpenAIClientFactory | None = None,
) -> WebSearchCompletionResult:
    """Call Bedrock Mantle Responses API with web_search enabled."""
    if not prompt.strip():
        raise BedrockWebSearchError("Prompt must be non-empty", error_code="VALIDATION_ERROR")
    if not api_key.strip():
        raise BedrockWebSearchError(
            "Bedrock API key is not configured",
            error_code="AUTH_FAILED",
        )
    validate_region_and_model(region, model_id)

    base_url = mantle_base_url(region)
    client = (
        client_factory()
        if client_factory is not None
        else AsyncOpenAI(api_key=api_key.strip(), base_url=base_url)
    )

    model_stripped = model_id.strip()
    tools = default_web_search_tools()
    request_payload = {
        "model": model_stripped,
        "input": prompt,
        "tools": tools,
    }
    dump_extra = {"base_url": base_url, "api": "responses.create"}

    try:
        response = await client.responses.create(
            model=model_stripped,
            input=prompt,
            tools=tools,
        )
    except APIStatusError as exc:
        dump_api_failure(
            adapter_name=ADAPTER_NAME_FOR_DUMP,
            request=request_payload,
            error=exc,
            model=model_stripped,
            extra=dump_extra,
        )
        logger.warning(
            "Bedrock Mantle responses.create failed status=%s",
            exc.status_code,
        )
        raise _map_api_error(exc) from exc
    except Exception as exc:
        dump_api_failure(
            adapter_name=ADAPTER_NAME_FOR_DUMP,
            request=request_payload,
            error=exc,
            model=model_stripped,
            extra=dump_extra,
        )
        logger.warning("Bedrock Mantle responses.create failed: %s", type(exc).__name__)
        raise BedrockWebSearchError(
            "Bedrock Mantle request failed",
            error_code="VALIDATION_ERROR",
        ) from exc

    text = _extract_output_text(response)
    citations = extract_citations_from_response_payload(response)
    return WebSearchCompletionResult(text=text, citations=citations)
