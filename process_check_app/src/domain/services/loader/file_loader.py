from typing import Any

from domain.services.enums.file_types import FileTypes
from domain.services.loader.factory.storage_provider_factory import (
    StorageProviderFactory,
)
from domain.services.loader.loader_types.config_loader import ConfigLoader
from domain.services.loader.loader_types.dataset_loader import DatasetLoader
from domain.services.loader.loader_types.test_config_loader import TestConfigLoader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class FileLoader:
    """
    FileLoader is responsible for loading files of various types such as datasets.

    This class uses specialized loaders for each file type and determines the appropriate storage adapter
    to fetch and instantiate the files.
    """

    # Dictionary mapping file types to their respective loaders
    _loaders = {
        "dataset": DatasetLoader,
        "test_config": TestConfigLoader,
        "config": ConfigLoader,
    }

    # Error message for unknown file types
    ERROR_UNKNOWN_FILE_TYPE = "[FileLoader] Unknown file type '{file_type}'"
    ERROR_LOADING_FILE = (
        "[FileLoader] Error loading file '{file_name}' of type '{file_type}': {error}"
    )

    @classmethod
    def load(cls, file_name: str, file_type: FileTypes) -> Any:
        """
        Load a file based on its name and type.

        This method determines the correct storage adapter and uses the specialized loader
        to fetch and instantiate the file.

        Args:
            file_name (str): The name of the file to be loaded.
            file_type (FileTypes): The type of the file to be loaded.

        Returns:
            Any: The loaded file instance.

        Raises:
            ValueError: If the file type is unknown.
            Exception: If there is an error during the loading process.
        """
        try:
            # Determine the correct storage adapter
            storage_adapter = StorageProviderFactory.get_adapter(file_name)

            # Select the correct loader based on the file type
            loader_cls = cls._loaders.get(file_type.name.lower())

            # Raise an error if the file type is unknown
            if not loader_cls:
                raise ValueError(
                    cls.ERROR_UNKNOWN_FILE_TYPE.format(file_type=file_type)
                )

            # Use the specialized loader to fetch and instantiate the file
            return loader_cls(storage_adapter).load(file_name)
        except Exception as e:
            # Log the error if loading fails
            logger.error(
                cls.ERROR_LOADING_FILE.format(
                    file_name=file_name, file_type=file_type, error=e
                )
            )
            raise
