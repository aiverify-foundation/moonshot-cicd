import os
from datetime import datetime
from typing import Any

from domain.entities.app_config_entity import AppConfigEntity
from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.loader.factory.file_format_factory import FileFormatFactory
from domain.services.loader.loader_types.loader import Loader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class ConfigLoader(Loader):
    """
    Responsible for loading configuration modules from various storage providers.

    This class uses a storage adapter to load the module and then uses the file format factory
    to deserialize the configuration module.
    """

    INFO_LOADING_CONFIG = "[ConfigLoader] Loading configuration module from {file_name} using {adapter_name}"
    ERROR_READING_FILE = "[ConfigLoader] Error reading file from {file_name}: {error}"
    ERROR_DESERIALIZING_CONTENT = (
        "[ConfigLoader] Error deserializing content from {file_name}: {error}"
    )
    WARNING_FAILED_TO_READ_FILE = (
        "[ConfigLoader] Failed to read file {file_name}: {error}"
    )
    ERROR_GETTING_CREATION_DATETIME = (
        "[ConfigLoader] Error getting creation datetime for {file_path}: {error}"
    )
    ERROR_FILE_NOT_FOUND = "[ConfigLoader] File not found: {file_name}"

    def __init__(self, storage_adapter: StorageProviderPort):
        """
        Initialize the ConfigLoader with a storage adapter.

        Args:
            storage_adapter (StorageProviderPort): The storage adapter to use for loading configurations.
        """
        self.storage_adapter = storage_adapter

    def load(self, loader_name: str) -> AppConfigEntity:
        """
        Load a configuration module from the specified file name.

        This method uses the storage adapter to read the file content from the given path
        and determines the correct file format adapter to deserialize the content.

        Args:
            loader_name (str): The name of the configuration module file.

        Returns:
            AppConfigEntity: The content of the configuration module if read and deserialized successfully.

        Raises:
            Exception: If there is an error reading or deserializing the file.
        """
        try:
            # Log the start of the loading process
            logger.info(
                self.INFO_LOADING_CONFIG.format(
                    file_name=loader_name,
                    adapter_name=self.storage_adapter.__class__.__name__,
                )
            )

            # Read the file content and its path
            file_content, file_name = self._read_file_content_and_path(loader_name)
            # Deserialize the file content
            deserialized_data = self._deserialize_content(file_name, file_content)

            return AppConfigEntity(**deserialized_data)
        except FileExistsError:
            raise FileNotFoundError
        except Exception as e:
            logger.error(self.ERROR_READING_FILE.format(file_name=loader_name, error=e))
            raise

    def _read_file_content_and_path(self, file_name: str) -> tuple[Any, str]:
        """
        Read the content and path of a specified file using the storage adapter.

        Args:
            file_name (str): The name of the configuration module file to be read.

        Returns:
            tuple[Any, str]: A tuple containing the content of the file and its complete path if read successfully.

        Raises:
            FileNotFoundError: If no valid file is found for the specified file name.
        """
        file_content = None

        try:
            # Attempt to read the file content using the storage adapter
            file_content = self.storage_adapter.read_file(file_name)
            if file_content:
                return file_content, file_name
            else:
                raise FileNotFoundError(
                    self.ERROR_FILE_NOT_FOUND.format(file_name=file_name)
                )
        except Exception as e:
            logger.warning(
                self.WARNING_FAILED_TO_READ_FILE.format(file_name=file_name, error=e)
            )
            raise

    def _deserialize_content(self, file_name: str, file_content: Any) -> Any:
        """
        Deserialize the file content using the appropriate file format adapter.

        Args:
            file_name (str): The name of the configuration module file.
            file_content (Any): The content of the file to be deserialized.

        Returns:
            Any: The deserialized content of the file.

        Raises:
            Exception: If there is an error deserializing the file content.
        """
        try:
            # Get the appropriate file format adapter
            file_format_adapter = FileFormatFactory.get_adapter(file_name)
            # Deserialize the file content
            return file_format_adapter.deserialize(file_content)
        except Exception as e:
            logger.error(
                self.ERROR_DESERIALIZING_CONTENT.format(file_name=file_name, error=e)
            )
            raise

    def _get_creation_datetime(self, file_path: str) -> datetime:
        """
        Get the creation datetime of the file.

        Args:
            file_path (str): The complete path of the file.

        Returns:
            datetime: The creation datetime of the file.
        """
        try:
            # Get the creation timestamp of the file
            timestamp = os.path.getctime(file_path)
            return datetime.fromtimestamp(timestamp)
        except Exception as e:
            logger.error(
                self.ERROR_GETTING_CREATION_DATETIME.format(
                    file_path=file_path, error=e
                )
            )
            raise
