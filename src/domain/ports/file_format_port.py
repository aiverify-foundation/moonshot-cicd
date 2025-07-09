from abc import ABC, abstractmethod
from typing import Any


class FileFormatPort(ABC):
    """
    Abstract base class for file format operations.

    This class defines the interface for serializing and deserializing data to and from
    specific file formats. Implementations of this class should provide concrete methods
    for these operations.
    """

    @staticmethod
    @abstractmethod
    def supports(path: str) -> bool:
        """
        Determine if the file format is supported for the given path.

        Args:
            path (str): The file path to check for support.

        Returns:
            bool: True if the file format is supported for the given path, otherwise False.
        """
        pass

    @abstractmethod
    def serialize(self, data: Any) -> str | None:
        """
        Serialize data into a specific file format.

        Args:
            data (Any): The data to be serialized.

        Returns:
            str | None: The serialized data as a string if successful, otherwise None.
        """
        pass

    @abstractmethod
    def deserialize(self, content: str) -> Any:
        """
        Deserialize data from a specific file format.

        Args:
            content (str): The content to be deserialized.

        Returns:
            Any: The deserialized data if successful, otherwise None.
        """
        pass
