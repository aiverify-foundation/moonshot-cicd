import copy
import json
import os
from typing import Any

import aiohttp

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

DEFAULT_API_TYPE = "POST"
DEFAULT_API_URL = "https://api.together.xyz/v1/chat/completions"

DEFAULT_API_BODY = (
    '{"model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", '
    '"messages": [{"role": "user", "content": ""}], "max_tokens": 128}'
)
DEFAULT_API_SECRET_ENV = "TOGETHER_API_KEY"


class CustomApiConnectorAdapter(ConnectorPort):
    """
    Adapter for sending HTTP requests to a custom API endpoint.

    Configuration is read from ConnectorEntity.params (populated from
    custom_app_config_parameters and custom_app_config_secrets in the DB).
    Supported param keys: api_type, api_url, api_body, api_key.

    ``api_body`` must be a JSON object. On each request, ``messages`` is built
    from the benchmark prompt (with optional pre/post/system prompts), while
    other keys (model, max_tokens, etc.) are taken from the template.
    """

    PROVIDER_NAME = "Custom API"
    SYSTEM_NAME = "custom_api_connector_adapter"
    VERSION = 1
    DEFAULT_CONFIG_PAIRS = {
        "api_type": DEFAULT_API_TYPE,
        "api_url": DEFAULT_API_URL,
        "api_body": DEFAULT_API_BODY,
    }

    WARNING_NO_API_SECRET = (
        "[CustomApiConnectorAdapter] WARNING: no api_key in connector params "
        "and {env_name} environment variable is not set or is empty."
    )
    INFO_CONFIGURED = (
        "[CustomApiConnectorAdapter] Configured with method: {method}, url: {url}"
    )
    INFO_API_SECRET_PRESENT = (
        "[CustomApiConnectorAdapter] API secret is present (length: {length} characters)"
    )
    INFO_MAKING_REQUEST = (
        "[CustomApiConnectorAdapter] Making API request: {method} {url}"
    )
    ERROR_PROCESSING_RESPONSE = (
        "[CustomApiConnectorAdapter] Failed to process API response."
    )
    ERROR_INVALID_API_BODY = (
        "[CustomApiConnectorAdapter] api_body must be a JSON object."
    )
    ERROR_EMPTY_RESPONSE = "The API did not return any response."
    ERROR_MISSING_CHOICES = "The API response is missing the expected choices field."
    ERROR_NO_CHOICES = "The API did not provide any response choices."
    ERROR_MISSING_MESSAGE = "The API response is missing the message field."
    ERROR_MISSING_CONTENT = "The API response is missing the content field."

    def configure(self, connector_entity: ConnectorEntity) -> None:
        self.connector_entity = connector_entity
        params = connector_entity.params or {}

        self.api_type = str(params.get("api_type", DEFAULT_API_TYPE)).upper()
        self.api_url = str(params.get("api_url", DEFAULT_API_URL))
        raw_body = str(params.get("api_body", DEFAULT_API_BODY))

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid api_body JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError(self.ERROR_INVALID_API_BODY)
        self._body_template: dict[str, Any] = parsed

        self.api_secret = str(params.get("api_key", "") or "").strip()
        if not self.api_secret:
            self.api_secret = (os.getenv(DEFAULT_API_SECRET_ENV) or "").strip()

        if self.api_secret:
            logger.info(
                self.INFO_API_SECRET_PRESENT.format(length=len(self.api_secret))
            )
        else:
            logger.warning(
                self.WARNING_NO_API_SECRET.format(env_name=DEFAULT_API_SECRET_ENV)
            )

        logger.info(
            self.INFO_CONFIGURED.format(method=self.api_type, url=self.api_url)
        )

    def _connector_prompt(self, prompt: Any) -> str:
        text = "" if prompt is None else str(prompt)
        return (
            f"{self.connector_entity.connector_pre_prompt}"
            f"{text}"
            f"{self.connector_entity.connector_post_prompt}"
        )

    def _build_messages(self, prompt: Any) -> list[dict[str, str]]:
        connector_prompt = self._connector_prompt(prompt)
        if self.connector_entity.system_prompt:
            return [
                {"role": "system", "content": self.connector_entity.system_prompt},
                {"role": "user", "content": connector_prompt},
            ]
        return [{"role": "user", "content": connector_prompt}]

    def _build_request_body(self, prompt: Any) -> dict[str, Any]:
        body = copy.deepcopy(self._body_template)
        body["messages"] = self._build_messages(prompt)
        return body

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        headers = {"Content-Type": "application/json"}
        if self.api_secret:
            headers["Authorization"] = f"Bearer {self.api_secret}"

        body = self._build_request_body(prompt)
        logger.info(
            self.INFO_MAKING_REQUEST.format(method=self.api_type, url=self.api_url)
        )

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=self.api_type,
                url=self.api_url,
                headers=headers,
                json=body,
            ) as response:
                response.raise_for_status()
                return ConnectorResponseEntity(
                    response=await self._process_response(response)
                )

    async def _process_response(self, response: aiohttp.ClientResponse) -> str:
        try:
            json_response = await response.json()

            if not json_response:
                raise ValueError(self.ERROR_EMPTY_RESPONSE)

            if "choices" not in json_response:
                raise ValueError(self.ERROR_MISSING_CHOICES)

            if not json_response["choices"]:
                raise ValueError(self.ERROR_NO_CHOICES)

            message = json_response["choices"][0].get("message")
            if message is None:
                raise ValueError(self.ERROR_MISSING_MESSAGE)

            content = message.get("content")
            if content is None:
                raise ValueError(self.ERROR_MISSING_CONTENT)

            return content
        except ValueError:
            raise
        except Exception as exc:
            logger.error(
                "%s Exception type: %s, Error: %s",
                self.ERROR_PROCESSING_RESPONSE,
                type(exc).__name__,
                exc,
            )
            raise
