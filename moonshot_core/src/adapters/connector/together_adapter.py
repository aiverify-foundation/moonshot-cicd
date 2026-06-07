import os
from typing import Any

from together import AsyncTogether

from application.services.provider_connector_env_key_service import ProviderConnectorEnvKeyService
from adapters.connector.strip_connector_chat_kwargs import (
    coerce_numeric_string_chat_params,
    strip_connector_keys_for_chat_completion,
)
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.app_config import AppConfig
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)

DEFAULT_MAX_ATTEMPTS = 3
_CHAT_COMPLETION_EXTRA_STRIP_KEYS = frozenset({"max_attempts", "max_concurrency"})


def _coerce_max_attempts(value: Any) -> int:
    if isinstance(value, str):
        try:
            value = int(float(value.strip()))
        except ValueError as exc:
            raise ValueError(f"max_attempts must be a valid integer, got {value!r}") from exc
    if not isinstance(value, int):
        raise ValueError("max_attempts must be of type int.")
    if value < 1:
        raise ValueError("max_attempts must be at least 1.")
    return value


def _resolve_max_attempts(connector_entity: ConnectorEntity) -> int:
    raw = connector_entity.params.get("max_attempts")
    if raw is None:
        raw = AppConfig().get_common_config("max_attempts")
    if raw in (None, {}):
        return DEFAULT_MAX_ATTEMPTS
    return _coerce_max_attempts(raw)


def _resolve_max_retries(connector_entity: ConnectorEntity) -> int:
    return max(0, _resolve_max_attempts(connector_entity) - 1)


class TogetherAdapter(ConnectorPort):
    PROVIDER_NAME = "TogetherAI"
    SYSTEM_NAME = "together_adapter"
    VERSION = 1
    DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    MODEL_TEXTBOX_EXPLANATION = (
        "Enter a TogetherAI model ID, e.g. meta-llama/Llama-3.3-70B-Instruct-Turbo"
    )
    DEFAULT_CONFIG_PAIRS = {
        "temperature": "0.7",
    }

    ERROR_PROCESSING_PROMPT = "[TogetherAdapter] Failed to process prompt."
    INFO_CONFIGURED = "[TogetherAdapter] Configured with model: {model}, endpoint: {endpoint}"
    WARNING_NO_API_KEY = "[TogetherAdapter] WARNING: TOGETHER_API_KEY environment variable is not set or is empty."
    INFO_API_KEY_PRESENT = "[TogetherAdapter] API key is present (length: {length} characters)"
    INFO_MAKING_REQUEST = "[TogetherAdapter] Making API request to model: {model}, endpoint: {endpoint}"

    """
    Adapter for interacting with the Together AI API.

    This class provides methods to configure the Together AI API client and retrieve responses
    based on given prompts. It uses the Together client to make requests to the Together AI API
    and processes the responses to return structured data.

    Attributes:
        connector_entity (ConnectorEntity): The configuration entity for the connector.
        _client (AsyncTogether): The Together AI API client.
    """

    def configure(self, connector_entity: ConnectorEntity):
        """
        Configure the Together AI API client with the given connector entity.

        Args:
            connector_entity (ConnectorEntity): The configuration entity for the connector.
        """
        self.connector_entity = connector_entity
        system_name, version = type(self).require_system_name_and_version()
        db_key = ProviderConnectorEnvKeyService().get_plain_api_key_for_provider_system_name(
            provider_system_name=system_name,
            version=version,
        )
        resolved_from_database = bool(db_key and db_key.strip())
        if resolved_from_database:
            api_key = db_key.strip()
        else:
            api_key = os.getenv("TOGETHER_API_KEY") or ""

        if api_key:
            if resolved_from_database:
                logger.info(
                    "[TogetherAdapter] API key resolved from database "
                    "(llm_provider system_name=%s, version=%s)",
                    system_name,
                    version,
                )
            else:
                logger.info("[TogetherAdapter] API key resolved from environment (TOGETHER_API_KEY)")
            logger.info(self.INFO_API_KEY_PRESENT.format(length=len(api_key)))
        else:
            logger.warning(self.WARNING_NO_API_KEY)
        
        endpoint = self.connector_entity.model_endpoint or "default (api.together.xyz/v1)"
        max_retries = _resolve_max_retries(connector_entity)
        logger.info(
            self.INFO_CONFIGURED.format(
                model=self.connector_entity.model,
                endpoint=endpoint
            )
        )
        logger.info(
            "[TogetherAdapter] Configured max_retries=%s (max_attempts=%s)",
            max_retries,
            max_retries + 1,
        )

        self._client = AsyncTogether(
            api_key=api_key,
            base_url=self.connector_entity.model_endpoint or None,
            max_retries=max_retries,
        )

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        """
        Retrieve a response from the Together AI API based on the given prompt.

        Args:
            prompt (Any): The prompt to send to the Together AI API. It can be of any type.

        Returns:
            ConnectorResponseEntity: The response from the Together AI API.
        """
        connector_prompt = f"{self.connector_entity.connector_pre_prompt}{prompt}{self.connector_entity.connector_post_prompt}"  # noqa: E501
        logger.info(f"Connector prompt: {connector_prompt}")
        if self.connector_entity.system_prompt:
            together_request = [
                {"role": "system", "content": self.connector_entity.system_prompt},
                {"role": "user", "content": connector_prompt},
            ]
        else:
            together_request = [{"role": "user", "content": connector_prompt}]

        # Merge model parameters with additional parameters
        new_params = {
            **self.connector_entity.params,
            "model": self.connector_entity.model,
            "messages": together_request,
        }
        new_params = coerce_numeric_string_chat_params(
            strip_connector_keys_for_chat_completion(
                new_params,
                extra_keys=_CHAT_COMPLETION_EXTRA_STRIP_KEYS,
            )
        )

        endpoint = self.connector_entity.model_endpoint or "default (api.together.xyz/v1)"
        logger.info(
            self.INFO_MAKING_REQUEST.format(
                model=self.connector_entity.model,
                endpoint=endpoint
            )
        )
        
        try:
            response = await self._client.chat.completions.create(**new_params)
            return ConnectorResponseEntity(
                response=await self._process_response(response)
            )
        except Exception as e:
            # Enhanced error logging with exception type and details
            error_type = type(e).__name__
            error_message = str(e)
            
            logger.error(
                f"{self.ERROR_PROCESSING_PROMPT} Exception type: {error_type}, "
                f"Error: {error_message}"
            )
            
            # Log additional context for common error types
            if "api_key" in error_message.lower() or "authentication" in error_message.lower():
                logger.error(
                    "[TogetherAdapter] Authentication error detected. "
                    "Please verify that TOGETHER_API_KEY environment variable is set correctly."
                )
            elif "connection" in error_message.lower() or "network" in error_message.lower():
                logger.error(
                    "[TogetherAdapter] Connection error detected. "
                    "Please check your network connection and API endpoint configuration."
                )
            elif "rate_limit" in error_message.lower() or "quota" in error_message.lower():
                logger.error(
                    "[TogetherAdapter] Rate limit or quota error detected. "
                    "Please check your API usage limits."
                )
            
            raise

    async def _process_response(self, response: Any) -> str:
        """
        Process the response from Together AI's API and return the message content as a string.

        This method processes the response received from Together AI's API call, specifically targeting
        the chat completion response structure. It extracts the message content from the first choice
        provided in the response, which is expected to contain the relevant information or answer.

        Args:
            response (Any): The response object received from a Together AI API call. It follows the
            structure of OpenAI-compatible chat completion response.

        Returns:
            str: A string containing the message content from the first choice in the response. This
            content represents the AI-generated text based on the input prompt.
        """
        return response.choices[0].message.content
