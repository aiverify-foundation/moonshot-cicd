from typing import Any

import yaml

from domain.ports.file_format_port import FileFormatPort
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class YamlAdapter(FileFormatPort):
    """
    Adapter for handling YAML file operations.

    This class provides methods to serialize data to YAML format and deserialize YAML content.
    It also logs errors encountered during these operations.
    """

    ERROR_SERIALIZE = "[YamlAdapter] Error serializing data to YAML: {error}"
    ERROR_DESERIALIZE = "[YamlAdapter] Error deserializing YAML content: {error}"

    SUFFIX = ".yaml"

    @staticmethod
    def supports(path: str) -> bool:
        """
        Determine if the YAML adapter supports the given path.

        Args:
            path (str): The path to check for support.

        Returns:
            bool: True if the path is supported by the YAML adapter, otherwise False.
        """
        return path.endswith(YamlAdapter.SUFFIX)

    def serialize(self, data: Any) -> str | None:
        """
        Serialize data to a YAML-formatted string.

        Args:
            data (Any): The data to be serialized.

        Returns:
            str | None: The YAML-formatted string if serialization is successful, otherwise None.
        """
        try:
            # Attempt to serialize the data to YAML format
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, set):
                        raise TypeError("Cannot serialize set type to YAML")

            return yaml.dump(data, default_flow_style=False)
        except Exception as e:
            # Log an error message if serialization fails
            logger.error(self.ERROR_SERIALIZE.format(error=e))
            return None

    def deserialize(self, content: str) -> Any:
        """
        Deserialize data from a YAML-formatted string.

        Args:
            content (str): The YAML content to be deserialized.

        Returns:
            Any: The deserialized data if successful, otherwise None.
        """
        try:
            # Attempt to deserialize the YAML content
            return yaml.safe_load(content)
        except Exception as e:
            # Log an error message if deserialization fails
            logger.error(self.ERROR_DESERIALIZE.format(error=e))
            return None
