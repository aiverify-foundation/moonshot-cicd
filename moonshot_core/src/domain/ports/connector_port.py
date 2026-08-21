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

    # Per-connector metadata (must be overridden by concrete adapters)
    PROVIDER_NAME: str
    SYSTEM_NAME: str
    VERSION: int
    DEFAULT_MODEL: str
    MODEL_TEXTBOX_EXPLANATION: str
    DEFAULT_CONFIG_PAIRS: dict[str, str]

    @classmethod
    def require_system_name_and_version(cls) -> tuple[str, int]:
        """
        Return ``(SYSTEM_NAME, VERSION)`` for resolving ``llm_provider`` rows in the database.

        Raises:
            TypeError: If ``SYSTEM_NAME`` is missing or blank, or ``VERSION`` is not an int.
        """
        name = getattr(cls, "SYSTEM_NAME", None)
        version = getattr(cls, "VERSION", None)
        if not isinstance(name, str) or not name.strip():
            raise TypeError(
                f"{cls.__name__} must define a non-empty SYSTEM_NAME class attribute (ConnectorPort)."
            )
        if not isinstance(version, int):
            raise TypeError(
                f"{cls.__name__} must define an int VERSION class attribute (ConnectorPort)."
            )
        return name.strip(), version

    @classmethod
    def provider_seed_definition(cls) -> dict:
        """Build provider seed dict (camelCase keys) from class metadata."""
        return {
            "name": cls.PROVIDER_NAME,
            "system_name": cls.SYSTEM_NAME,
            "version": cls.VERSION,
            "defaultModel": cls.DEFAULT_MODEL,
            "modelTextboxExplanation": cls.MODEL_TEXTBOX_EXPLANATION,
            "defaultConfigPairs": cls.DEFAULT_CONFIG_PAIRS,
        }

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
