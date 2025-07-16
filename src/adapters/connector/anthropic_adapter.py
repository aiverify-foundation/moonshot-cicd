import os
import anthropic

from typing import Any

from anthropic import AsyncAnthropic

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger


# Initialize a logger for this module
logger = configure_logger(__name__)


class AnthropicAdapter(ConnectorPort):
    """
    Adapter for interacting with the Anthropic API.

    This class provides methods to configure the Anthropic API client and retrieve responses
    based on given prompts. It uses the AsyncAnthropic client to make asynchronous requests
    to the Anthropic API and processes the responses to return structured data.

    Attributes:
        connector_entity: The configuration entity for the connector.
        _client (Anthropic): The Anthropic API client.
    """

    REQUIRED_PARAMETERS = ["model", "max_tokens", "messages"]

    def configure(self, connector_entity: ConnectorEntity):
        """
        Configure the Anthropic API client with the given connector entity.

        Args:
            connector_entity: The configuration entity for the connector.
        """
        assert (
            connector_entity and connector_entity.params
            and 'max_tokens' in connector_entity.params
            ), "AnthropicAdapter.configure::Max tokens not specified/valid."

        max_tokens = connector_entity.params['max_tokens']
        assert isinstance(connector_entity.params['max_tokens'], int) and max_tokens >= 1, \
            f'AnthropicAdapter.configure::Max tokens must be >=1, "{max_tokens}" provided.'

        assert connector_entity.model, "AnthropicAdapter.configure::Model not specified."

        self.connector_entity = connector_entity
        self._client = AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY") or "",
            base_url=self.connector_entity.model_endpoint or None,
        )

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        """
        Retrieve a response from the Anthropic API based on the given prompt.

        Args:
            prompt (Any): The prompt to send to the Anthropic API. It can be of any type.

        Returns:
            ConnectorResponseEntity: The response from the Anthropic API.
        """
        connector_prompt = self.connector_entity.connector_pre_prompt + prompt \
            + self.connector_entity.connector_post_prompt

        try:
            func_params = {
                **self.connector_entity.params,
                "model": self.connector_entity.model,
                "system": self.connector_entity.system_prompt,
                "messages": [{"role": "user", "content": connector_prompt}]
            }

            assert all([param in func_params for param in self.REQUIRED_PARAMETERS]), \
                "AnthropicAdapter.get_response::Required parameters are missing."

            messages = await self._client.messages.create(**func_params)

            return ConnectorResponseEntity(response=messages.content[0].text)

        except anthropic.APIConnectionError as e:
            logger.error("AnthropicAdapter.get_response::The server could not be reached: %s", e.__cause__)
            raise e
        except anthropic.AuthenticationError as e:
            logger.error("AnthropicAdapter.get_response::HTTP 401 - Authentication failed: %s", e.__cause__)
            raise e
        except anthropic.RateLimitError as e:
            logger.error("AnthropicAdapter.get_response::HTTP 429 - Rate limit exceeded: %s", e.__cause__)
            raise e
        except Exception as e:
            logger.error("AnthropicAdapter.get_response::Error processing prompt: %s", e.__cause__)
            raise e
