import os
from typing import Any

from langchain_openai.chat_models import ChatOpenAI

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class LangchainOpenAIChatOpenAIAdapter(ConnectorPort):
    def configure(self, connector_entity: ConnectorEntity):
        """
        Configure the Langchain OpenAI API client with the given connector entity.

        Args:
            connector_entity (ConnectorEntity): The configuration entity for the connector.
        """
        self.connector_entity = connector_entity
        self._client = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY") or "",
            model=self.connector_entity.model or None,
            base_url=self.connector_entity.model_endpoint or None,
        )

    def get_client(self) -> Any:
        """
        Retrieve the ChatOpenAI client instance.

        This method returns the Langchain ChatOpenAI client instance that is used to interact with the
        Langchain ChatOpenAI API.

        Returns:
            Any: The Langchain ChatOpenAI client instance.
        """
        return self._client

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        """
        This method is not implemented and will raise a NotImplementedError.

        Args:
            prompt (str): The input prompt to send to the Langchain ChatOpenAI API.

        Returns:
            ConnectorResponse: This method does not return a response as it is not implemented.

        Raises:
            NotImplementedError: Always raised to indicate this method is not implemented.
        """
        raise NotImplementedError(
            "This connector is not supposed to generate response."
        )
