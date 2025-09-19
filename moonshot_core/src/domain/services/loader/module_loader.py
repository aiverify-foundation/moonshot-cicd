from typing import Any, Tuple

from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.factory.storage_provider_factory import (
    StorageProviderFactory,
)
from domain.services.loader.loader_types.attack_module_loader import (
    AttackModuleLoader,
)
from domain.services.loader.loader_types.connector_loader import ConnectorLoader
from domain.services.loader.loader_types.metric_loader import MetricLoader
from domain.services.loader.loader_types.prompt_processor_loader import (
    PromptProcessorLoader,
)
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class ModuleLoader:
    """
    ModuleLoader is responsible for loading various types of modules such as metrics, connectors, and prompt processors.

    This class uses specialized loaders for each module type and determines the appropriate storage adapter
    to fetch and instantiate the modules.
    """

    # Dictionary mapping module types to their respective loaders
    _loaders = {
        "metric": MetricLoader,
        "connector": ConnectorLoader,
        "prompt_processor": PromptProcessorLoader,
        "attack_module": AttackModuleLoader,
    }

    # Error messages
    ERROR_UNKNOWN_MODULE_TYPE = "[ModuleLoader] Unknown module type '{module_type}'"
    ERROR_LOADING_MODULE = "[ModuleLoader] Error loading module '{module_name}' of type '{module_type}': {error}"

    @classmethod
    def load(cls, module_name: str, module_type: ModuleTypes) -> Tuple[Any, str]:
        """
        Load a module based on its name and type.

        This method determines the correct storage adapter and uses the specialized loader
        to fetch and instantiate the module.

        Args:
            module_name (str): The name of the module to be loaded.
            module_type (ModuleTypes): The type of the module to be loaded.

        Returns:
            Tuple[Any, str]: A tuple containing the loaded module instance and the ID of the instance.

        Raises:
            ValueError: If the module type is unknown.
            Exception: If there is an error during the loading process.
        """
        try:
            # Determine the correct storage adapter
            storage_adapter = StorageProviderFactory.get_adapter(module_name)

            # Select the correct loader based on the module type
            loader_cls = cls._loaders.get(module_type.name.lower())

            # Raise an error if the module type is unknown
            if not loader_cls:
                raise ValueError(
                    cls.ERROR_UNKNOWN_MODULE_TYPE.format(module_type=module_type)
                )

            # Use the specialized loader to fetch and instantiate the module
            return loader_cls(storage_adapter).load(module_name)
        except Exception as e:
            # Log the error if loading fails
            logger.error(
                cls.ERROR_LOADING_MODULE.format(
                    module_name=module_name, module_type=module_type, error=e
                )
            )
            raise (e)
