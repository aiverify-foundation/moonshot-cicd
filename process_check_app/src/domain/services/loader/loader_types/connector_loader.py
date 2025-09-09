import os
from typing import Tuple

from domain.ports.connector_port import ConnectorPort
from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.app_config import AppConfig
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.factory.storage_provider_factory import (
    StorageProviderFactory,
)
from domain.services.loader.loader_types.loader import Loader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class ConnectorLoader(Loader):
    """
    Responsible for loading connector modules from various storage providers.

    This class uses a storage adapter to load the module and then uses the module importer
    to instantiate the connector module.
    """

    INFO_LOADING_CONNECTOR = "[ConnectorLoader] Loading connector module from {connector_name} using {adapter_name}"
    ERROR_LOADING_CONNECTOR = "[ConnectorLoader] Error loading connector module from {connector_name}: {error}"

    def __init__(self, storage_adapter: StorageProviderPort):
        """
        Initialize the ConnectorLoader with a storage adapter.

        Args:
            storage_adapter (StorageProviderPort): The storage adapter to use for loading modules.
        """
        self.storage_adapter = storage_adapter

    def load(self, loader_name: str) -> Tuple[ConnectorPort, str]:
        """
        Load a connector module by its name.

        This method uses the storage adapter to read the file content from the specified path
        and then uses the module importer to create an instance of the connector module.

        Args:
            loader_name (str): The name of the connector module file.

        Returns:
            ConnectorPort: An instance of ConnectorPort if the module is loaded successfully.

        Raises:
            ValueError: If the file type is unsupported.
            Exception: If there is an error loading the connector module.
        """
        try:
            # Log the start of the loading process
            logger.info(
                self.INFO_LOADING_CONNECTOR.format(
                    connector_name=loader_name,
                    adapter_name=self.storage_adapter.__class__.__name__,
                )
            )

            # Check if the current storage adapter is the fallback adapter
            if isinstance(
                self.storage_adapter, StorageProviderFactory._fallback_adapter
            ):
                # Construct the complete path to the metric module file
                complete_path = os.path.join(
                    AppConfig.DEFAULT_ADAPTERS_PATH,
                    ModuleTypes.CONNECTOR.name.lower(),
                    f"{loader_name}.py",
                )
            else:
                complete_path = f"{loader_name}.py"

            # Use the storage adapter to load the module
            return self.storage_adapter.load_module(
                loader_name, ModuleTypes.CONNECTOR, complete_path
            )
        except Exception as e:
            # Log the error if loading fails
            logger.error(
                self.ERROR_LOADING_CONNECTOR.format(connector_name=loader_name, error=e)
            )
            raise
