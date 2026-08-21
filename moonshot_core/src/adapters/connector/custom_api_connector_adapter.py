import copy
import json
import os
from typing import Any

import aiohttp
from jsonpath_ng.ext import parse
from jsonpath_ng.exceptions import JsonPathParserError

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

DEFAULT_API_TYPE = "POST"
DEFAULT_API_URL = "https://api.together.xyz/v1/chat/completions"

DEFAULT_API_BODY = json.dumps(
    {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": [{"role": "user", "content": "{{prompt}}"}],
    },
    indent=2,
)
DEFAULT_API_SECRET_ENV = "TOGETHER_API_KEY"
DEFAULT_API_KEY_AUTH_SCHEME = "bearer"
DEFAULT_RESPONSE_PATH = "choices[0].message.content"
PROMPT_PLACEHOLDER = "{{prompt}}"


class CustomApiConnectorAdapter(ConnectorPort):
    """
    Adapter for sending HTTP requests to a custom API endpoint.

    Configuration is read from ConnectorEntity.params (populated from
    custom_app_config_parameters and custom_app_config_secrets in the DB).
    Supported param keys: api_type, api_url, api_body, response_path, api_key,
    api_key_auth_scheme, api_key_auth_custom_header, headers (JSON object of extra
    request headers).

    ``response_path`` is a JSONPath expression used to read the model reply from
    the API JSON response (default: ``choices[0].message.content``).

    ``api_body`` must be a JSON object containing the ``{{prompt}}`` placeholder.
    On each request, every ``{{prompt}}`` in the template is replaced with the
    benchmark prompt (including optional pre/post prompts).
    """

    PROVIDER_NAME = "Custom API"
    SYSTEM_NAME = "custom_api_connector_adapter"
    VERSION = 1
    DEFAULT_CONFIG_PAIRS = {
        "api_type": DEFAULT_API_TYPE,
        "api_url": DEFAULT_API_URL,
        "api_body": DEFAULT_API_BODY,
        "response_path": DEFAULT_RESPONSE_PATH,
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
    ERROR_MISSING_PROMPT_PLACEHOLDER = (
        "[CustomApiConnectorAdapter] api_body must include the "
        "'{{prompt}}' placeholder."
    )
    ERROR_EMPTY_RESPONSE = "The API did not return any response."
    ERROR_INVALID_RESPONSE_PATH = (
        "[CustomApiConnectorAdapter] response_path must be a non-empty JSONPath expression."
    )
    ERROR_RESPONSE_PATH_NOT_FOUND = (
        "No value found at response_path '{path}' in the API response."
    )
    ERROR_RESPONSE_PATH_NOT_SCALAR = (
        "The value at response_path '{path}' must be a scalar, not an object or array."
    )

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
        if PROMPT_PLACEHOLDER not in raw_body:
            raise ValueError(self.ERROR_MISSING_PROMPT_PLACEHOLDER)
        self._body_template: dict[str, Any] = parsed

        self.api_secret = str(params.get("api_key", "") or "").strip()
        if not self.api_secret:
            self.api_secret = (os.getenv(DEFAULT_API_SECRET_ENV) or "").strip()

        self.api_key_auth_scheme = str(
            params.get("api_key_auth_scheme", DEFAULT_API_KEY_AUTH_SCHEME)
            or DEFAULT_API_KEY_AUTH_SCHEME
        ).strip().lower()
        self.api_key_auth_custom_header = str(
            params.get("api_key_auth_custom_header", "") or ""
        ).lstrip()

        self._custom_headers: dict[str, str] = {}
        raw_headers = str(params.get("headers", "") or "").strip()
        if raw_headers:
            try:
                parsed_headers = json.loads(raw_headers)
                if isinstance(parsed_headers, dict):
                    self._custom_headers = {
                        str(key): str(value) for key, value in parsed_headers.items()
                    }
            except json.JSONDecodeError:
                logger.warning(
                    "[CustomApiConnectorAdapter] Invalid headers JSON; ignoring."
                )

        self.response_path = str(
            params.get("response_path", DEFAULT_RESPONSE_PATH) or DEFAULT_RESPONSE_PATH
        ).strip()
        if not self.response_path:
            raise ValueError(self.ERROR_INVALID_RESPONSE_PATH)
        try:
            parse(self.response_path)
        except JsonPathParserError as exc:
            raise ValueError(
                f"Invalid response_path JSONPath: {exc}"
            ) from exc

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

    def _inject_prompt(self, value: Any, prompt_text: str) -> Any:
        if isinstance(value, str):
            return value.replace(PROMPT_PLACEHOLDER, prompt_text)
        if isinstance(value, dict):
            return {key: self._inject_prompt(item, prompt_text) for key, item in value.items()}
        if isinstance(value, list):
            return [self._inject_prompt(item, prompt_text) for item in value]
        return value

    def _build_request_body(self, prompt: Any) -> dict[str, Any]:
        connector_prompt = self._connector_prompt(prompt)
        body = copy.deepcopy(self._body_template)
        injected = self._inject_prompt(body, connector_prompt)
        if not isinstance(injected, dict):
            raise ValueError(self.ERROR_INVALID_API_BODY)
        return injected

    def _build_auth_header(self) -> tuple[str, str] | None:
        if not self.api_secret:
            return None

        scheme = self.api_key_auth_scheme or DEFAULT_API_KEY_AUTH_SCHEME
        if scheme == "authorization_api_key":
            return "Authorization", f"ApiKey {self.api_secret}"
        if scheme == "x_api_key":
            return "X-API-Key", self.api_secret
        if scheme == "x_api_key_lower":
            return "x-api-key", self.api_secret
        if scheme == "custom":
            header_name = self.api_key_auth_custom_header.lstrip()
            if not header_name:
                logger.warning(
                    "[CustomApiConnectorAdapter] Custom auth header name is empty; "
                    "skipping API key header."
                )
                return None
            return header_name, self.api_secret

        return "Authorization", f"Bearer {self.api_secret}"

    def _build_request_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        headers.update(self._custom_headers)
        auth_header = self._build_auth_header()
        if auth_header:
            header_name, header_value = auth_header
            headers[header_name] = header_value
        return headers

    async def probe(self, prompt: Any) -> tuple[int, str]:
        headers = self._build_request_headers()
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
                return response.status, await response.text()

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        headers = self._build_request_headers()
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

    def _extract_response_value(self, json_response: Any) -> str:
        if json_response is None or json_response == "":
            raise ValueError(self.ERROR_EMPTY_RESPONSE)

        matches = parse(self.response_path).find(json_response)
        if not matches:
            raise ValueError(
                self.ERROR_RESPONSE_PATH_NOT_FOUND.format(path=self.response_path)
            )

        value = matches[0].value
        if isinstance(value, (dict, list)):
            raise ValueError(
                self.ERROR_RESPONSE_PATH_NOT_SCALAR.format(path=self.response_path)
            )
        if isinstance(value, str):
            return value
        return json.dumps(value)

    async def _process_response(self, response: aiohttp.ClientResponse) -> str:
        try:
            json_response = await response.json()
            return self._extract_response_value(json_response)
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
