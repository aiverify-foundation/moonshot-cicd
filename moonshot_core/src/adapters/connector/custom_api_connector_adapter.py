import os
from typing import Any

import aiohttp

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

API_TYPE = "POST"
API_URL = "https://api.together.xyz/v1/chat/completions"
API_BODY = (
    '{"model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", '
    '"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 128}'
)
API_SECRET_ENV = "TOGETHER_API_KEY"


class CustomApiConnectorAdapter(ConnectorPort):
    """
    Adapter for sending a fixed HTTP request to a custom API endpoint.

    Edit the module-level constants (API_TYPE, API_URL, API_BODY, API_SECRET_ENV)
    at the top of this file to change the request. The prompt passed to get_response
    is ignored; the body is fully static.
    """

    WARNING_NO_API_SECRET = (
        "[CustomApiConnectorAdapter] WARNING: {env_name} environment variable "
        "is not set or is empty."
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
    ERROR_EMPTY_RESPONSE = "The API did not return any response."
    ERROR_MISSING_CHOICES = "The API response is missing the expected choices field."
    ERROR_NO_CHOICES = "The API did not provide any response choices."
    ERROR_MISSING_MESSAGE = "The API response is missing the message field."
    ERROR_MISSING_CONTENT = "The API response is missing the content field."

    def configure(self, connector_entity: ConnectorEntity) -> None:
        self.connector_entity = connector_entity
        self.api_secret = (os.getenv(API_SECRET_ENV) or "").strip()

        if self.api_secret:
            logger.info(
                self.INFO_API_SECRET_PRESENT.format(length=len(self.api_secret))
            )
        else:
            logger.warning(self.WARNING_NO_API_SECRET.format(env_name=API_SECRET_ENV))

        logger.info(
            self.INFO_CONFIGURED.format(method=API_TYPE.upper(), url=API_URL)
        )

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        headers = {"Content-Type": "application/json"}
        if self.api_secret:
            headers["Authorization"] = f"Bearer {self.api_secret}"

        logger.info(
            self.INFO_MAKING_REQUEST.format(method=API_TYPE.upper(), url=API_URL)
        )

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=API_TYPE.upper(),
                url=API_URL,
                headers=headers,
                data=API_BODY,
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
