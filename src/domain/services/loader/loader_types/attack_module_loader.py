import os
from typing import Tuple

from domain.ports.attack_module_port import AttackModulePort
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


class AttackModuleLoader(Loader):
    """
    Responsible for loading attack modules from various storage providers.

    This class uses a storage adapter to load the module and then uses the module importer
    to instantiate the attack module.
    """

    INFO_LOADING_ATTACK_MODULE = "[AttackModuleLoader] Loading attack module from {attack_module_name} using {adapter_name}"  # noqa: E501
    ERROR_LOADING_ATTACK_MODULE = "[AttackModuleLoader] Error loading attack module from {attack_module_name}: {error}"

    def __init__(self, storage_adapter: StorageProviderPort):
        """
        Initialize the AttackModuleLoader with a storage adapter.

        Args:
            storage_adapter (StorageProviderPort): The storage adapter to use for loading attack modules.
        """
        self.storage_adapter = storage_adapter

    def load(self, loader_name: str) -> Tuple[AttackModulePort, str]:
        """
        Load an attack module by its name.

        This method uses the storage adapter to read the file content from the specified path
        and then uses the module importer to create an instance of the attack module.

        Args:
            loader_name (str): The name of the attack module file.

        Returns:
            AttackModulePort: An instance of AttackModulePort if the module is loaded successfully.

        Raises:
            ValueError: If the file type is unsupported.
            Exception: If there is an error loading the attack module.
        """
        try:
            # Log the start of the loading process
            logger.info(
                self.INFO_LOADING_ATTACK_MODULE.format(
                    attack_module_name=loader_name,
                    adapter_name=self.storage_adapter.__class__.__name__,
                )
            )

            # Check if the current storage adapter is the fallback adapter
            if isinstance(
                self.storage_adapter, StorageProviderFactory._fallback_adapter
            ):
                complete_path = os.path.join(
                    AppConfig.DEFAULT_ATTACK_MODULES_PATH,
                    f"{loader_name}.py",
                )
            else:
                complete_path = f"{loader_name}.py"

            # Use the storage adapter to load the module
            return self.storage_adapter.load_module(
                loader_name, ModuleTypes.ATTACK_MODULE, complete_path
            )
        except Exception as e:
            # Log the error if loading fails
            logger.error(
                self.ERROR_LOADING_ATTACK_MODULE.format(
                    attack_module_name=loader_name, error=e
                )
            )
            raise (e)
