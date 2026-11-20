import json
import os
import re
from typing import Any, Literal

from adapters.connector.custom_api_connector_adapter import CustomApiConnectorAdapter
from domain.entities.connector_entity import ConnectorEntity
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

DEFAULT_BEDROCK_REGION = "us-east-1"
DEFAULT_BEDROCK_MODEL = "openai.gpt-oss-20b-1:0"
DEFAULT_BEDROCK_API_URL = (
    f"https://bedrock-runtime.{DEFAULT_BEDROCK_REGION}.amazonaws.com"
    f"/model/{DEFAULT_BEDROCK_MODEL}/converse"
)
DEFAULT_BEDROCK_API_BODY = json.dumps(
    {
        "messages": [
            {
                "role": "user",
                "content": [{"text": "{{prompt}}"}],
            }
        ],
    },
    indent=2,
)
DEFAULT_BEDROCK_RESPONSE_PATH = "output.message.content[0].text"
DEFAULT_BEDROCK_API_SECRET_ENV = "AWS_BEARER_TOKEN_BEDROCK"

INFERENCE_PROFILE_PREFIXES = ("us.", "eu.", "global.")
CONVERSE_MODEL_PATH_PATTERN = re.compile(r"/model/([^/]+)/converse")
OPENAI_RESPONSES_URL_MARKER = "/openai/v1/responses"

BedrockApiFormat = Literal["converse", "responses"]
ModelFamily = Literal["anthropic", "openai", "unknown"]

ERROR_INVALID_BEDROCK_RESPONSE = (
    "Bedrock API response for model '{model_id}' is not a JSON object."
)
ERROR_MISSING_CONVERSE_CONTENT = (
    "Bedrock Converse response for model '{model_id}' is missing "
    "output.message.content."
)
ERROR_INVALID_CONVERSE_CONTENT = (
    "Bedrock Converse response for model '{model_id}' has invalid "
    "output.message.content (expected a list)."
)
ERROR_NO_CONVERSE_TEXT_BLOCKS = (
    "Bedrock Converse response for model '{model_id}' has no text content blocks "
    "(content block types seen: {block_types})."
)
ERROR_INVALID_RESPONSES_OUTPUT = (
    "Bedrock OpenAI Responses response for model '{model_id}' has invalid "
    "output (expected a list)."
)
ERROR_NO_RESPONSES_TEXT = (
    "Bedrock OpenAI Responses response for model '{model_id}' has no output_text "
    "content (output item types seen: {output_types})."
)
ERROR_UNRECOGNIZED_BEDROCK_OUTPUT = (
    "Bedrock API response for model '{model_id}' has unrecognized output shape."
)
WARNING_NO_CONVERSE_TEXT_BLOCKS = (
    "[BedrockApiConnectorAdapter] No text blocks in Converse response for model "
    "'{model_id}' (content block types: {block_types})."
)
WARNING_NO_RESPONSES_TEXT = (
    "[BedrockApiConnectorAdapter] No output_text in OpenAI Responses response for "
    "model '{model_id}' (output item types: {output_types})."
)
WARNING_BEDROCK_URL_RESPONSE_FORMAT_MISMATCH = (
    "[BedrockApiConnectorAdapter] Configured URL suggests {url_format} but response "
    "body looks like {response_format}; using response body for extraction."
)


def _infer_bedrock_api_format_from_url(api_url: str) -> BedrockApiFormat | None:
    normalized = (api_url or "").lower()
    if CONVERSE_MODEL_PATH_PATTERN.search(normalized) or normalized.rstrip("/").endswith(
        "/converse"
    ):
        return "converse"
    if OPENAI_RESPONSES_URL_MARKER in normalized or normalized.rstrip("/").endswith(
        "/responses"
    ):
        return "responses"
    return None


def _classify_bedrock_response_format(
    json_response: dict[str, Any],
) -> BedrockApiFormat | None:
    output = json_response.get("output")
    if isinstance(output, dict) and isinstance(output.get("message"), dict):
        return "converse"
    if isinstance(output, list):
        return "responses"
    if json_response.get("object") == "response":
        return "responses"
    return None


def _parse_model_id_from_converse_url(api_url: str) -> str | None:
    match = CONVERSE_MODEL_PATH_PATTERN.search(api_url or "")
    if not match:
        return None
    return match.group(1)


def _model_id_from_json_response(json_response: Any) -> str | None:
    if not isinstance(json_response, dict):
        return None
    model = json_response.get("model")
    if isinstance(model, str) and model.strip():
        return model.strip()
    return None


def _model_id_from_request_template(adapter: "BedrockApiConnectorAdapter") -> str | None:
    model = adapter._body_template.get("model")
    if isinstance(model, str) and model.strip():
        return model.strip()
    return None


def _strip_inference_profile_prefix(model_id: str) -> str:
    normalized = model_id
    while True:
        lowered = normalized.lower()
        stripped = False
        for prefix in INFERENCE_PROFILE_PREFIXES:
            if lowered.startswith(prefix):
                normalized = normalized[len(prefix) :]
                stripped = True
                break
        if not stripped:
            break
    return normalized


def _detect_model_family(model_id: str) -> ModelFamily:
    normalized = _strip_inference_profile_prefix(model_id).lower()
    if normalized.startswith("anthropic."):
        return "anthropic"
    if normalized.startswith("openai."):
        return "openai"
    return "unknown"


def _resolve_configured_model_id(
    adapter: "BedrockApiConnectorAdapter",
    json_response: Any = None,
) -> str:
    model = (adapter.connector_entity.model or "").strip()
    if model:
        return model
    parsed = _parse_model_id_from_converse_url(adapter.api_url)
    if parsed:
        return parsed
    from_body = _model_id_from_request_template(adapter)
    if from_body:
        return from_body
    from_response = _model_id_from_json_response(json_response)
    if from_response:
        return from_response
    return "unknown"


def _content_block_types(content: list[Any]) -> list[str]:
    types: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            types.append("invalid")
            continue
        if "text" in block:
            types.append("text")
        elif "reasoningContent" in block:
            types.append("reasoningContent")
        elif "toolUse" in block:
            types.append("toolUse")
        elif "toolResult" in block:
            types.append("toolResult")
        else:
            keys = [key for key in block if key]
            types.append(keys[0] if keys else "empty")
    return types


def _responses_output_item_types(output: list[Any]) -> list[str]:
    types: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            types.append("invalid")
            continue
        item_type = item.get("type")
        types.append(str(item_type) if item_type is not None else "unknown")
    return types


def _extract_converse_assistant_text(json_response: dict[str, Any], model_id: str) -> str:
    _detect_model_family(model_id)

    output = json_response.get("output")
    message = output.get("message") if isinstance(output, dict) else None
    content = message.get("content") if isinstance(message, dict) else None

    if content is None:
        raise ValueError(ERROR_MISSING_CONVERSE_CONTENT.format(model_id=model_id))
    if not isinstance(content, list):
        raise ValueError(ERROR_INVALID_CONVERSE_CONTENT.format(model_id=model_id))

    text_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if "reasoningContent" in block:
            continue
        text_value = block.get("text")
        if isinstance(text_value, str):
            text_parts.append(text_value)

    if not text_parts:
        block_types = _content_block_types(content)
        block_types_label = ", ".join(block_types) if block_types else "none"
        logger.warning(
            WARNING_NO_CONVERSE_TEXT_BLOCKS.format(
                model_id=model_id,
                block_types=block_types_label,
            )
        )
        raise ValueError(
            ERROR_NO_CONVERSE_TEXT_BLOCKS.format(
                model_id=model_id,
                block_types=block_types_label,
            )
        )

    return "".join(text_parts)


def _extract_openai_responses_assistant_text(
    json_response: dict[str, Any],
    model_id: str,
) -> str:
    _detect_model_family(model_id)

    output_text = json_response.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text

    output = json_response.get("output")
    if not isinstance(output, list):
        raise ValueError(ERROR_INVALID_RESPONSES_OUTPUT.format(model_id=model_id))

    text_parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "reasoning":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "output_text":
                text_value = part.get("text")
                if isinstance(text_value, str):
                    text_parts.append(text_value)

    if not text_parts:
        output_types = _responses_output_item_types(output)
        output_types_label = ", ".join(output_types) if output_types else "none"
        logger.warning(
            WARNING_NO_RESPONSES_TEXT.format(
                model_id=model_id,
                output_types=output_types_label,
            )
        )
        raise ValueError(
            ERROR_NO_RESPONSES_TEXT.format(
                model_id=model_id,
                output_types=output_types_label,
            )
        )

    return "".join(text_parts)


def _extract_bedrock_assistant_text(
    json_response: Any,
    model_id: str,
    *,
    configured_url: str = "",
) -> str:
    if not isinstance(json_response, dict):
        raise ValueError(ERROR_INVALID_BEDROCK_RESPONSE.format(model_id=model_id))

    response_format = _classify_bedrock_response_format(json_response)
    url_format = _infer_bedrock_api_format_from_url(configured_url)
    if (
        response_format is not None
        and url_format is not None
        and response_format != url_format
    ):
        logger.warning(
            WARNING_BEDROCK_URL_RESPONSE_FORMAT_MISMATCH.format(
                url_format=url_format,
                response_format=response_format,
            )
        )

    if response_format == "converse":
        return _extract_converse_assistant_text(json_response, model_id)
    if response_format == "responses":
        return _extract_openai_responses_assistant_text(json_response, model_id)

    if url_format == "converse":
        return _extract_converse_assistant_text(json_response, model_id)
    if url_format == "responses":
        return _extract_openai_responses_assistant_text(json_response, model_id)

    raise ValueError(ERROR_UNRECOGNIZED_BEDROCK_OUTPUT.format(model_id=model_id))


class BedrockApiConnectorAdapter(CustomApiConnectorAdapter):
    """
    HTTP adapter for AWS Bedrock with Bedrock API key (Bearer) auth.

    Supports Converse (``output.message.content`` text blocks) and the OpenAI
    Responses API on Bedrock (``output[]`` message items with ``output_text``).
    Reasoning blocks are skipped in both formats. The ``response_path`` param is
    kept for configure/DB compatibility only and is not used for extraction.
    """

    PROVIDER_NAME = "AWS Bedrock API"
    SYSTEM_NAME = "bedrock_api_connector_adapter"
    VERSION = 1
    DEFAULT_API_SECRET_ENV = DEFAULT_BEDROCK_API_SECRET_ENV
    DEFAULT_CONFIG_PAIRS = {
        "api_type": "POST",
        "api_url": DEFAULT_BEDROCK_API_URL,
        "api_body": DEFAULT_BEDROCK_API_BODY,
        "response_path": DEFAULT_BEDROCK_RESPONSE_PATH,
        "api_key_auth_scheme": "bearer",
    }

    def configure(self, connector_entity: ConnectorEntity) -> None:
        super().configure(connector_entity)
        params = connector_entity.params or {}
        if str(params.get("api_key", "") or "").strip():
            return
        self.api_secret = (os.getenv(DEFAULT_BEDROCK_API_SECRET_ENV) or "").strip()

    def _extract_response_value(self, json_response: Any) -> str:
        model_id = _resolve_configured_model_id(self, json_response)
        return _extract_bedrock_assistant_text(
            json_response,
            model_id,
            configured_url=self.api_url,
        )
