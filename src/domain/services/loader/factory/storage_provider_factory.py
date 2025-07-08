import os
from typing import Optional

from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.app_config import AppConfig
from domain.services.loader.module_import.module_importer import get_instance
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class StorageProviderFactory:
    """
    Factory class to automatically register and select storage adapters.

    This class is responsible for discovering, registering, and selecting the appropriate
    storage adapter based on the given path.
    """

    _adapters: list[type[StorageProviderPort]] = []  # List to store registered adapters
    _fallback_adapter_name: str = "LocalStorageAdapter"  # Name of the fallback adapter
    _fallback_adapter: Optional[type[StorageProviderPort]] = (
        None  # This will be set to LocalStorageAdapter later
    )

    # Class attributes for logging messages
    INFO_REGISTER_ADAPTER = (
        "[StorageProviderFactory] Storage Provider Adapter '{adapter_cls}' registered."
    )
    WARNING_NO_ADAPTER_FOUND = "[StorageProviderFactory] No specific adapter found for '{path}', falling back to LocalStorageAdapter."  # noqa: E501
    ERROR_NO_FALLBACK_ADAPTER = "[StorageProviderFactory] No fallback adapter is set."
    ERROR_INVALID_ADAPTER = (
        "[StorageProviderFactory] {adapter_cls} must subclass StorageProviderPort"
    )
    INFO_DETECTED_ADAPTER = (
        "[StorageProviderFactory] Detected storage provider adapter: {adapter_cls}"
    )
    ERROR_DISCOVER_ADAPTER = (
        "[StorageProviderFactory] Error discovering adapter: {error}"
    )
    INFO_SET_FALLBACK_ADAPTER = (
        "[StorageProviderFactory] LocalStorageAdapter set as fallback adapter."
    )
    ERROR_LOADING_ADAPTER = (
        "[StorageProviderFactory] Error loading adapter for path '{path}': {error}"
    )
    ERROR_INITIAL_DISCOVERY = (
        "[StorageProviderFactory] Error during initial discovery of adapters: {error}"
    )

    @classmethod
    def discover_adapters(cls) -> None:
        """
        Automatically discover and register all subclasses of StorageProviderPort.

        This method scans the 'storage_provider' directory for Python files, attempts to
        instantiate each module, and registers it if it is a subclass of StorageProviderPort.
        """
        folder_path = os.path.join(AppConfig.DEFAULT_ADAPTERS_PATH, "storage_provider")
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".py"):
                module_name = file_name[:-3]  # Remove the .py extension
                try:
                    instance = get_instance(
                        module_name, os.path.join(folder_path, file_name)
                    )
                    if instance and issubclass(instance.__class__, StorageProviderPort):
                        cls._adapters.append(instance.__class__)
                        logger.info(
                            cls.INFO_DETECTED_ADAPTER.format(
                                adapter_cls=instance.__class__.__name__
                            )
                        )

                        # Set the fallback adapter if it matches the fallback adapter name
                        if instance.__class__.__name__ == cls._fallback_adapter_name:
                            cls._fallback_adapter = instance.__class__
                            logger.info(cls.INFO_SET_FALLBACK_ADAPTER)
                except Exception as error:
                    logger.error(cls.ERROR_DISCOVER_ADAPTER.format(error=error))

    @classmethod
    def register_adapter(cls, adapter_cls: type[StorageProviderPort]) -> None:
        """
        Register a custom storage adapter.

        Args:
            adapter_cls (type[StorageProviderPort]): The adapter class to register.

        Raises:
            TypeError: If the adapter_cls does not subclass StorageProviderPort.
        """
        if not issubclass(adapter_cls, StorageProviderPort):
            raise TypeError(
                cls.ERROR_INVALID_ADAPTER.format(adapter_cls=adapter_cls.__name__)
            )

        cls._adapters.append(adapter_cls)
        logger.info(cls.INFO_REGISTER_ADAPTER.format(adapter_cls=adapter_cls.__name__))

    @classmethod
    def get_adapter(cls, path: str) -> StorageProviderPort:
        """
        Find and return the appropriate adapter for the given path.

        This method iterates through the registered adapters to find one that supports
        the given path. If no specific adapter is found, it falls back to the default adapter.

        Args:
            path (str): The path to find an adapter for.

        Returns:
            StorageProviderPort: An instance of the appropriate storage adapter.

        Raises:
            RuntimeError: If no fallback adapter is set.
        """
        try:
            if not cls._adapters:
                cls.discover_adapters()  # Ensure adapters are discovered

            for adapter_cls in cls._adapters:
                if adapter_cls is cls._fallback_adapter:
                    continue
                if hasattr(adapter_cls, "supports") and adapter_cls.supports(path):
                    return adapter_cls()

            # Log a warning and fall back to the local storage adapter
            logger.warning(cls.WARNING_NO_ADAPTER_FOUND.format(path=path))
            if cls._fallback_adapter is None:
                raise RuntimeError(cls.ERROR_NO_FALLBACK_ADAPTER)
            return cls._fallback_adapter()
        except Exception as error:
            logger.error(cls.ERROR_LOADING_ADAPTER.format(path=path, error=error))
            raise


# Automatically discover and register built-in adapters
try:
    StorageProviderFactory.discover_adapters()
except Exception as error:
    logger.error(StorageProviderFactory.ERROR_INITIAL_DISCOVERY.format(error=error))
