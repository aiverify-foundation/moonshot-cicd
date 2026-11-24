import os
from typing import Tuple

from domain.ports.metric_port import MetricPort
from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.benchmark_extensions import (
    adapter_not_found_error,
    resolve_adapter_module_path,
)
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.factory.storage_provider_factory import (
    StorageProviderFactory,
)
from domain.services.loader.loader_types.loader import Loader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class MetricLoader(Loader):
    """
    Responsible for loading metric modules from various storage providers.

    This class uses a storage adapter to load the module and then uses the module importer
    to instantiate the metric module.
    """

    INFO_LOADING_METRIC = (
        "[MetricLoader] Loading metric module from {metric_name} using {adapter_name}"
    )
    ERROR_LOADING_METRIC = (
        "[MetricLoader] Error loading metric module from {metric_name}: {error}"
    )

    def __init__(self, storage_adapter: StorageProviderPort):
        """
        Initialize the MetricLoader with a storage adapter.

        Args:
            storage_adapter (StorageProviderPort): The storage adapter to use for loading metric modules.
        """
        self.storage_adapter = storage_adapter

    def load(self, loader_name: str) -> Tuple[MetricPort, str]:
        """
        Load a metric module by its name.

        This method uses the storage adapter to read the file content from the specified path
        and then uses the module importer to create an instance of the metric module.

        Args:
            loader_name (str): The name of the metric module file.

        Returns:
            MetricPort: An instance of MetricPort if the module is loaded successfully.

        Raises:
            ValueError: If the file type is unsupported.
            Exception: If there is an error loading the metric module.
        """
        try:
            # Log the start of the loading process
            logger.info(
                self.INFO_LOADING_METRIC.format(
                    metric_name=loader_name,
                    adapter_name=self.storage_adapter.__class__.__name__,
                )
            )

            # Check if the current storage adapter is the fallback adapter
            is_local_fallback = isinstance(
                self.storage_adapter, StorageProviderFactory._fallback_adapter
            )
            if is_local_fallback:
                # Prefer an extension adapter, then the built-in metric module.
                complete_path = resolve_adapter_module_path(
                    ModuleTypes.METRIC, loader_name
                )
            else:
                complete_path = f"{loader_name}.py"

            # Use the storage adapter to load the module
            try:
                return self.storage_adapter.load_module(
                    loader_name, ModuleTypes.METRIC, complete_path
                )
            except FileNotFoundError as e:
                # Only a missing adapter file is reported as AdapterNotFoundError.
                if not is_local_fallback or os.path.exists(complete_path):
                    raise
                raise adapter_not_found_error(ModuleTypes.METRIC, loader_name) from e
        except Exception as e:
            # Log the error if loading fails
            logger.error(
                self.ERROR_LOADING_METRIC.format(metric_name=loader_name, error=e)
            )
            raise
