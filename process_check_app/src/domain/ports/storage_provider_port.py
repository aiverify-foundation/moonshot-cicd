from abc import ABC, abstractmethod
from typing import Any, Tuple


class StorageProviderPort(ABC):
    """
    Abstract base class for storage provider operations.

    This class defines the interface for various storage operations such as loading modules,
    reading files, writing files, and listing files in a storage provider. Implementations
    of this class should provide concrete methods for these operations.
    """

    PREFIX = ""

    @staticmethod
    @abstractmethod
    def supports(path: str) -> bool:
        """
        Check if the storage provider supports the given path.

        Args:
            path (str): The path to check for support.

        Returns:
            bool: True if the storage provider supports the given path, otherwise False.
        """
        pass

    @abstractmethod
    def load_module(
        self, file_path: str, module_type: Any, complete_path: str
    ) -> Tuple[Any, str]:
        """
        Load a module from the storage provider.

        Args:
            file_path (str): The path of the module to be loaded.
            complete_path (str): The complete path of the module to be loaded.

        Returns:
            Any: The content of the module if loaded successfully, otherwise None.
        """
        pass

    @abstractmethod
    def read_file(self, file_path: str) -> Any:
        """
        Read the content of a file from the storage provider.

        Args:
            file_path (str): The path of the file to be read.

        Returns:
            Any: The content of the file if read successfully, otherwise None.
        """
        pass

    @abstractmethod
    def write_file(self, file_path: str, content: Any) -> bool:
        """
        Write content to a file in the storage provider.

        Args:
            file_path (str): The path where the file will be stored.
            content (Any): The content to be saved to the file.

        Returns:
            bool: True if the content is saved successfully, otherwise False.
        """
        pass

    @abstractmethod
    def list(self, directory_path: str) -> list[str]:
        """
        List all files in a specified directory in the storage provider.

        Args:
            directory_path (str): The path to the directory whose files are to be listed.

        Returns:
            list[str]: A list of file names in the specified directory.
        """
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        Check if a file exists in the storage provider.

        Args:
            file_path (str): The path of the file to check.

        Returns:
            bool: True if the file exists, otherwise False.
        """
        pass

    @abstractmethod
    def get_creation_datetime(self, file_path: str) -> str:
        """
        Get the creation datetime of a file from the storage provider.

        Args:
            file_path (str): The path of the file whose creation datetime is to be retrieved.

        Returns:
            str: The creation datetime of the file as a string.
        """
        pass
