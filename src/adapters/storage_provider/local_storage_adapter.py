import os
from typing import Any, Tuple

from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.loader.module_import.module_importer import get_instance
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class LocalStorageAdapter(StorageProviderPort):
    """
    LocalStorageAdapter is a storage provider adapter for handling local file operations.

    This class provides methods to read, write, and list files in a local file system.
    It also includes error handling and logging for file operations.
    """

    PREFIX = None

    SUCCESS_WRITE_FILE = (
        "[LocalStorageAdapter] File written successfully at: {file_path}"
    )
    ERROR_WRITE_FILE = "[LocalStorageAdapter] Error writing file: {error}"
    ERROR_READ_FILE = "[LocalStorageAdapter] Error reading file: {error}"
    FILE_EXIST_ERROR = "[LocalStorageAdapter] File already exists at: {file_path}"
    WARNING_FILE_NOT_FOUND = "[LocalStorageAdapter] File not found: {file_path}"
    ERROR_LIST_FILE = (
        "[LocalStorageAdapter] Error listing files in {directory_path}: {error}"
    )
    ERROR_LOADING_MODULE = "[LocalStorageAdapter] Error loading metric module: {error}"

    @staticmethod
    def supports(path: str) -> bool:
        """
        Always return True as this is a fallback adapter.

        Args:
            path (str): The path to check for support.

        Returns:
            bool: Always True.
        """
        return True

    def load_module(
        self, file_path: str, module_type: Any, complete_path: str
    ) -> Tuple[Any, str]:
        """
        Load a module from the local storage.

        Args:
            file_path (str): The path of the module to be loaded.
            module_type (Any): Local Storage Adapter do not need this field.
            complete_path (str): The complete path of the module to be loaded.

        Returns:
            Tuple[Any, str]: An instance of the module and the file ID if loaded successfully,
                otherwise raises an exception.

        Raises:
            Exception: If there is an error loading the module.
        """
        try:
            instance = get_instance(file_path, complete_path)
            if instance is None:
                raise Exception(f"Failed to load module from path {complete_path}")
            return instance, file_path
        except Exception as e:
            logger.error(self.ERROR_LOADING_MODULE.format(error=e))
            raise

    def read_file(self, file_path: str) -> Any:
        """
        Read the content of a file from the local storage.

        Args:
            file_path (str): The path of the file to be read.

        Returns:
            Any: The content of the file if read successfully, otherwise None.
        """
        try:
            with open(file_path, "r") as file:
                content = file.read()
            return content
        except FileNotFoundError:
            logger.warning(self.WARNING_FILE_NOT_FOUND.format(file_path=file_path))
            return None
        except Exception as e:
            logger.error(self.ERROR_READ_FILE.format(error=e))
            return None

    def write_file(self, file_path: str, content: Any) -> tuple[bool, str]:
        """
        Write content to a file in the local storage.

        Args:
            file_path (str): The path where the file will be stored.
            content (Any): The content to be saved to the file.

        Returns:
            tuple[bool, str]: A tuple containing a boolean indicating success and a message.
        """
        try:
            # Create directory if it does not exist
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Check if the file already exists
            if self.exists(file_path):
                raise FileExistsError()

            # Write content to the file
            with open(file_path, "w") as file:
                file.write(content)
            logger.info(self.SUCCESS_WRITE_FILE.format(file_path=file_path))
            return True, "File written successfully"
        except FileExistsError:
            logger.error(self.FILE_EXIST_ERROR.format(file_path=file_path))
            return False, "File already exists"
        except Exception as e:
            logger.error(self.ERROR_WRITE_FILE.format(error=e))
            return False, str(e)

    def list(self, directory_path: str) -> list[str]:
        """
        List all files in a specified directory in the local storage.

        Args:
            directory_path (str): The path to the directory whose files are to be listed.

        Returns:
            list[str]: A list of file names in the specified directory.
        """
        try:
            files = os.listdir(directory_path)
            return files
        except Exception as e:
            logger.error(
                self.ERROR_LIST_FILE.format(directory_path=directory_path, error=e)
            )

    def exists(self, file_path: str) -> bool:
        """
        Check if a file exists at the specified path in the local file system.

        Args:
            file_path (str): The path to the file to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return os.path.exists(file_path)

    def get_creation_datetime(self, file_path: str) -> float:
        """
        Get the creation datetime of a file in the local storage.

        Args:
            file_path (str): The path of the file whose creation datetime is to be retrieved.

        Returns:
            float: The creation datetime of the file as a timestamp.
        """
        return os.path.getctime(file_path)
