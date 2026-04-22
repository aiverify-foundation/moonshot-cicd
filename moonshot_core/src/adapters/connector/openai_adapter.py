import os
from typing import Any

from openai import AsyncOpenAI, BadRequestError

from adapters.connector.strip_connector_chat_kwargs import (
    coerce_numeric_string_chat_params,
    strip_connector_keys_for_chat_completion,
)
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class OpenAIAdapter(ConnectorPort):
    PROVIDER_NAME = "OpenAI"
    SYSTEM_NAME = "openai_adapter"
    VERSION = 1
    DEFAULT_MODEL = "gpt-4o-mini"
    MODEL_TEXTBOX_EXPLANATION = "Enter an OpenAI model name, e.g. gpt-4o-mini"
    DEFAULT_CONFIG_PAIRS = {
        "base_url": "https://api.openai.com/v1",
        "api_type": "openai",
    }

    ERROR_PROCESSING_PROMPT = "[OpenAIAdapter] Failed to process prompt."
    LOG_UNSUPPORTED_CHAT_KWARG = (
        "[OpenAIAdapter] Unsupported keyword argument for chat.completions.create"
    )
    LOG_API_REJECTED_CHAT = (
        "[OpenAIAdapter] API rejected the chat completion request (invalid parameters)"
    )

    """
    Adapter for interacting with the OpenAI API.

    This class provides methods to configure the OpenAI API client and retrieve responses
    based on given prompts. It uses the AsyncOpenAI client to make asynchronous requests
    to the OpenAI API and processes the responses to return structured data.

    Attributes:
        connector_entity (ConnectorEntity): The configuration entity for the connector.
        _client (AsyncOpenAI): The OpenAI API client.
    """

    def configure(self, connector_entity: ConnectorEntity):
        """
        Configure the OpenAI API client with the given connector entity.

        Args:
            connector_entity (ConnectorEntity): The configuration entity for the connector.
        """
        self.connector_entity = connector_entity
        self._client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY") or "",
            base_url=self.connector_entity.model_endpoint or None,
        )

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        """
        Retrieve a response from the OpenAI API based on the given prompt.

        Args:
            prompt (Any): The prompt to send to the OpenAI API. It can be of any type.

        Returns:
            ConnectorResponseEntity: The response from the OpenAI API.
        """
        connector_prompt = f"{self.connector_entity.connector_pre_prompt}{prompt}{self.connector_entity.connector_post_prompt}"  # noqa: E501

        if self.connector_entity.system_prompt:
            openai_request = [
                {"role": "system", "content": self.connector_entity.system_prompt},
                {"role": "user", "content": connector_prompt},
            ]
        else:
            openai_request = [{"role": "user", "content": connector_prompt}]

        # Merge model parameters with additional parameters
        new_params = {
            **self.connector_entity.params,
            "model": self.connector_entity.model,
            "messages": openai_request,
        }
        create_kwargs = coerce_numeric_string_chat_params(
            strip_connector_keys_for_chat_completion(new_params)
        )
        try:
            response = await self._client.chat.completions.create(**create_kwargs)
            return ConnectorResponseEntity(
                response=await self._process_response(response)
            )
        except TypeError as e:
            if "unexpected keyword argument" in str(e).lower():
                param_keys = sorted(self.connector_entity.params)
                logger.error(
                    f"{self.LOG_UNSUPPORTED_CHAT_KWARG}: {e} "
                    f"connector_param_keys={param_keys}"
                )
            else:
                logger.error(f"{self.ERROR_PROCESSING_PROMPT} {e}")
            raise
        except BadRequestError as e:
            logger.error(f"{self.LOG_API_REJECTED_CHAT}: {e}")
            raise
        except Exception as e:
            logger.error(f"{self.ERROR_PROCESSING_PROMPT} {e}")
            raise

    async def _process_response(self, response: Any) -> str:
        """
        Process the response from OpenAI's API and return the message content as a string.

        This method processes the response received from OpenAI's API call, specifically targeting
        the chat completion response structure. It extracts the message content from the first choice
        provided in the response, which is expected to contain the relevant information or answer.

        Args:
            response (Any): The response object received from an OpenAI API call. It is expected to
            follow the structure of OpenAI's chat completion response.

        Returns:
            str: A string containing the message content from the first choice in the response. This
            content represents the AI-generated text based on the input prompt.
        """
        return response.choices[0].message.content
