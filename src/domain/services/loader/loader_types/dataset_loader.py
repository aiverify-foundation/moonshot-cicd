from datetime import datetime
from typing import Any

from domain.entities.dataset_entity import DatasetEntity
from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.app_config import AppConfig
from domain.services.loader.factory.file_format_factory import FileFormatFactory
from domain.services.loader.loader_types.loader import Loader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class DatasetLoader(Loader):
    """
    Responsible for loading dataset modules from various storage providers.

    This class uses a storage adapter to load the module and then uses the file format factory
    to deserialize the dataset module.
    """

    DEFAULT_DATASET_FORMAT = ".json"
    FILE_PATH_PREFIX = ""

    INFO_LOADING_DATASET = (
        "[DatasetLoader] Loading dataset module from {file_name} using {adapter_name}"
    )
    ERROR_READING_FILE = "[DatasetLoader] Error reading file from {file_name}: {error}"
    ERROR_DESERIALIZING_CONTENT = (
        "[DatasetLoader] Error deserializing content from {file_name}: {error}"
    )
    WARNING_FAILED_TO_READ_FILE = (
        "[DatasetLoader] Failed to read file {complete_path}: {error}"
    )
    ERROR_NO_VALID_FILE_FOUND = (
        "[DatasetLoader] No valid file found for {file_name} in {directory_path}"
    )
    ERROR_GETTING_CREATION_DATETIME = (
        "[DatasetLoader] Error getting creation datetime for {file_path}: {error}"
    )

    def __init__(self, storage_adapter: StorageProviderPort):
        """
        Initialize the DatasetLoader with a storage adapter.

        Args:
            storage_adapter (StorageProviderPort): The storage adapter to use for loading datasets.
        """
        self.storage_adapter = storage_adapter
        self.set_dataset_prefix()

    def load(self, loader_name: str) -> DatasetEntity:
        """
        Load a dataset module from the specified file name.

        This method uses the storage adapter to read the file content from the given path
        and determines the correct file format adapter to deserialize the content.

        Args:
            loader_name (str): The name of the dataset module file.

        Returns:
            DatasetEntity: The content of the dataset module if read and deserialized successfully.

        Raises:
            Exception: If there is an error reading or deserializing the file.
        """
        try:
            # Log the start of the loading process
            logger.info(
                self.INFO_LOADING_DATASET.format(
                    file_name=loader_name,
                    adapter_name=self.storage_adapter.__class__.__name__,
                )
            )

            file_content, complete_path = self._read_file_content_and_path(loader_name)
            json_data = self._deserialize_content(complete_path, file_content)
            json_data["id"] = json_data.get("name", "default_id")
            json_data["num_of_dataset_prompts"] = len(json_data.get("examples", []))

            creation_datetime = self._get_creation_datetime(complete_path)
            json_data["created_date"] = creation_datetime.strftime("%Y-%m-%d %H:%M:%S")

            return DatasetEntity(**json_data)
        except Exception as e:
            logger.error(self.ERROR_READING_FILE.format(file_name=loader_name, error=e))
            raise

    def _read_file_content_and_path(self, file_name: str) -> tuple[Any, str]:
        """
        Read the content and path of a specified file using the storage adapter.

        Args:
            file_name (str): The name of the dataset module file to be read.

        Returns:
            tuple[Any, str]: A tuple containing the content of the file and its complete path if read successfully.

        Raises:
            FileNotFoundError: If no valid file is found for the specified file name.
        """
        # Construct the complete path with the default dataset format
        complete_path = (
            f"{self.FILE_PATH_PREFIX}{file_name}{self.DEFAULT_DATASET_FORMAT}"
        )
        # Check if the file exists using the storage adapter
        if self.storage_adapter.exists(complete_path):
            try:
                # Attempt to read the file content
                file_content = self.storage_adapter.read_file(complete_path)
                if file_content:
                    return file_content, file_name
            except Exception as e:
                # Log a warning if reading the file fails
                logger.warning(
                    self.WARNING_FAILED_TO_READ_FILE.format(
                        complete_path=complete_path, error=e
                    )
                )

        # Raise an error if no valid file is found
        raise FileNotFoundError(
            self.ERROR_NO_VALID_FILE_FOUND.format(
                file_name=file_name, directory_path=AppConfig.DEFAULT_DATASETS_PATH
            )
        )

    def _deserialize_content(self, file_name: str, file_content: Any) -> Any:
        """
        Deserialize the file content using the appropriate file format adapter.

        Args:
            file_name (str): The name of the dataset module file.
            file_content (Any): The content of the file to be deserialized.

        Returns:
            Any: The deserialized content of the file.

        Raises:
            Exception: If there is an error deserializing the file content.
        """
        try:
            file_format_adapter = FileFormatFactory.get_adapter(file_name)
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
            complete_path = (
                f"{self.FILE_PATH_PREFIX}{file_path}{self.DEFAULT_DATASET_FORMAT}"
            )
            timestamp = self.storage_adapter.get_creation_datetime(complete_path)
            return datetime.fromtimestamp(timestamp)
        except Exception as e:
            logger.error(
                self.ERROR_GETTING_CREATION_DATETIME.format(
                    file_path=complete_path, error=e
                )
            )
            raise

    def set_dataset_prefix(self):
        """
        Set the dataset file path prefix.

        This method checks if the storage adapter's PREFIX attribute is None,
        indicating that the default path should be used. If so, it sets the
        FILE_PATH_PREFIX to the default datasets path defined in the AppConfig,
        appending a trailing slash to ensure proper path construction.

        This ensures that all dataset file paths are correctly prefixed with
        the appropriate directory path when using the default storage settings.
        """
        if self.storage_adapter.PREFIX is None:
            self.FILE_PATH_PREFIX = AppConfig.DEFAULT_DATASETS_PATH + "/"
