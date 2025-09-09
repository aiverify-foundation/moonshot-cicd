from abc import ABC, abstractmethod
from typing import Any

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity


class ConnectorPort(ABC):
    """
    Abstract base class for connector operations.

    This class defines the interface for configuring connectors and obtaining responses from them.
    Implementations of this class should provide concrete methods for these operations.
    """

    @abstractmethod
    def configure(self, connector_entity: ConnectorEntity) -> None:
        """
        Configure the connector with the given entity.

        Args:
            connector_entity (ConnectorEntity): The entity containing the configuration details for the connector.
        """
        pass

    @abstractmethod
    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        """
        Get a response from the connector based on the provided prompt.

        Args:
            prompt (Any): The prompt or input data for which a response is needed.

        Returns:
            ConnectorResponseEntity: The response entity containing the result from the connector.
        """
        pass
