import os

from domain.ports.prompt_processor_port import PromptProcessorPort
from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.app_config import AppConfig
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.loader_types.loader import Loader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class PromptProcessorLoader(Loader):
    """
    Responsible for loading prompt processor modules from various storage providers.

    This class uses a storage adapter to load the module and then uses the module importer
    to instantiate the prompt processor module.
    """

    INFO_LOADING_PROMPT_PROCESSOR = "[PromptProcessorLoader] Loading prompt processor module from {prompt_processor_name} using {adapter_name}"  # noqa: E501
    ERROR_LOADING_PROMPT_PROCESSOR = "[PromptProcessorLoader] Error loading prompt processor module from {prompt_processor_name}: {error}"  # noqa: E501

    def __init__(self, storage_adapter: StorageProviderPort):
        """
        Initialize the PromptProcessorLoader with a storage adapter.

        Args:
            storage_adapter (StorageProviderPort): The storage adapter to use for loading modules.
        """
        self.storage_adapter = storage_adapter

    def load(self, loader_name: str) -> PromptProcessorPort:
        """
        Load a prompt processor module by its name.

        This method uses the storage adapter to read the file content from the specified path
        and then uses the module importer to create an instance of the prompt processor module.

        Args:
            loader_name (str): The name of the prompt processor module file.

        Returns:
            PromptProcessorPort: An instance of PromptProcessorPort if the module is loaded successfully.

        Raises:
            ValueError: If the file type is unsupported.
            Exception: If there is an error loading the prompt processor module.
        """
        try:
            # Log the start of the loading process
            logger.info(
                self.INFO_LOADING_PROMPT_PROCESSOR.format(
                    prompt_processor_name=loader_name,
                    adapter_name=self.storage_adapter.__class__.__name__,
                )
            )

            # Construct the complete path to the prompt processor module file
            complete_path = os.path.join(
                AppConfig.DEFAULT_ADAPTERS_PATH,
                ModuleTypes.PROMPT_PROCESSOR.name.lower(),
                f"{loader_name}.py",
            )

            # Use the storage adapter to load the module
            return self.storage_adapter.load_module(
                loader_name, ModuleTypes.PROMPT_PROCESSOR, complete_path
            )
        except Exception as e:
            # Log the error if loading fails
            logger.error(
                self.ERROR_LOADING_PROMPT_PROCESSOR.format(
                    prompt_processor_name=loader_name, error=e
                )
            )
            raise
