import json
from typing import Any

from domain.ports.file_format_port import FileFormatPort
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class JsonAdapter(FileFormatPort):
    """
    Adapter for handling JSON file operations.

    This class provides methods to serialize data to JSON format and deserialize JSON content.
    It also logs errors encountered during these operations.
    """

    ERROR_SERIALIZE = "[JsonAdapter] Error serializing data to JSON: {error}"
    ERROR_DESERIALIZE = "[JsonAdapter] Error deserializing JSON content: {error}"
    ERROR_READING_FILE = "[JsonAdapter] Error reading file {file_path}: {error}"

    SUFFIX = ".json"

    @staticmethod
    def supports(path: str) -> bool:
        """
        Determine if the JSON adapter supports the given path.

        Args:
            path (str): The path to check for support.

        Returns:
            bool: True if the path is supported by the JSON adapter, otherwise False.
        """
        return path.endswith(JsonAdapter.SUFFIX)

    def serialize(self, data: Any) -> str | None:
        """
        Serialize data to a JSON-formatted string.

        Args:
            data (Any): The data to be serialized.

        Returns:
            str | None: The JSON-formatted string if serialization is successful, otherwise None.
        """
        try:
            # Attempt to serialize the data to JSON format
            return json.dumps(data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # Log an error message if serialization fails
            logger.error(self.ERROR_SERIALIZE.format(error=e))
            return None

    def deserialize(self, content: str) -> Any:
        """
        Deserialize data from a JSON-formatted string.

        Args:
            content (str): The JSON content to be deserialized.

        Returns:
            Any: The deserialized data if successful, otherwise None.
        """
        try:
            # Attempt to deserialize the JSON content
            return json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            # Log an error message if deserialization fails
            logger.error(self.ERROR_DESERIALIZE.format(error=e))
            return None
