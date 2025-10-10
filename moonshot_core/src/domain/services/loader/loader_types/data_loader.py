from typing import Any, Dict
from typing import List

from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.app_config import AppConfig
from domain.services.loader.factory.file_format_factory import FileFormatFactory
from domain.services.loader.loader_types.loader import Loader
from domain.services.logger import configure_logger
from domain.entities.test_config_entity import TestConfigEntity
from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.test_bundle_entity import TestBundleEntity
from application.services.wrappers.bundle_entity_wrapper import TestBundleEntityWrapper
from application.services.wrappers.benchmark_test_entity_wrapper import BenchmarkTestEntityWrapper

# Initialize a logger for this module
logger = configure_logger(__name__)


class DataLoader(Loader):
    """
    Responsible for loading data configuration modules from various storage providers.

    This class uses a storage adapter to load the module and then uses the file format factory
    to deserialize the data configuration module.
    """

    DEFAULT_DATA_FORMAT = ".yaml"
    FILE_PATH_PREFIX = ""

    INFO_LOADING_DATA = "[DataLoader] Loading data configuration module from {file_name} using {adapter_name}"  # noqa: E501
    ERROR_READING_FILE = (
        "[DataLoader] Error reading file from {file_name}: {error}"
    )
    ERROR_DESERIALIZING_CONTENT = (
        "[DataLoader] Error deserializing content from {file_name}: {error}"
    )
    WARNING_FAILED_TO_READ_FILE = (
        "[DataLoader] Failed to read file {complete_path}: {error}"
    )
    ERROR_NO_VALID_FILE_FOUND = (
        "[DataLoader] No valid file found for {file_name} in {directory_path}"
    )

    def __init__(self, storage_adapter: StorageProviderPort):
        """
        Initialize the DataLoader with a storage adapter.

        Args:
            storage_adapter (StorageProviderPort): The storage adapter to use for loading data configurations.
        """
        self.storage_adapter = storage_adapter
        self._set_data_prefix()

    def load(self, loader_name: str) -> tuple[Dict[str, List[TestBundleEntityWrapper]], Dict[str, List[BenchmarkTestEntityWrapper]]]:
        """
        Load a data configuration module from the specified file name.

        This method uses the storage adapter to read the file content from the given path
        and determines the correct file format adapter to deserialize the content.

        Args:
            loader_name (str): The name of the data configuration module file.

        Returns:
            dict[str, list[DataEntity]]: A dictionary where keys are top-level YAML keys
            and values are lists of data configuration entities if read and deserialized successfully.
        Raises:
            Exception: If there is an error reading or deserializing the file.
        """
        try:
            # Log the start of the loading process
            logger.info(
                self.INFO_LOADING_DATA.format(
                    file_name=loader_name,
                    adapter_name=self.storage_adapter.__class__.__name__,
                )
            )
            
            file_content, complete_path = self._read_file_content_and_path(loader_name)
            yaml_data = self._deserialize_content(complete_path, file_content)
            benchmark_test_wrapper_entities = {}
            bundle_wrapper_entities = {}
            # Iterate over all top-level keys in the YAML data
            for key, config_data in yaml_data.items():
                tests = config_data["tests"]
                description = config_data.get("description", "")
                category = config_data.get("category", "")
                name = config_data.get("name", key)  # Use the key as default name if name is not provided

                # Create BenchmarkTestEntity objects for individual tests
                for test in tests:
                    benchmark_test_entity = BenchmarkTestEntity(
                        name=test.get("name"),
                        id=test.get("name"),  # test id will be name for now
                        dataset=None,  # Will be resolved later
                        metric=test.get("metric"),
                        description=test.get("description", "")
                    )
                    wrapper = BenchmarkTestEntityWrapper(benchmark_test_entity)
                    wrapper.dataset_name = test.get("dataset", "")
                    benchmark_test_wrapper_entities[test.get("name")] = wrapper

                # Create BenchmarkTestEntity objects for the bundle
                bundle_tests = []
                for test in tests:
                    benchmark_test_entity = BenchmarkTestEntity(
                        name=test.get("name"),
                        id=test.get("name"),  # test id will be name for now
                        dataset=None,  # Will be resolved later
                        metric=test.get("metric"),
                        description=test.get("description", "")
                    )
                    bundle_tests.append(benchmark_test_entity)
                
                # Create bundle wrapper entity
                bundle_wrapper = TestBundleEntityWrapper(
                    name=name,
                    tests=bundle_tests,
                    description=description,
                    category=category,
                    id=key
                )
                bundle_wrapper_entities[key] = bundle_wrapper
            return (benchmark_test_wrapper_entities, bundle_wrapper_entities)
        except FileExistsError:
            raise FileNotFoundError
        except Exception as e:
            logger.error(self.ERROR_READING_FILE.format(file_name=loader_name, error=e))
            raise

    def _read_file_content_and_path(self, file_name: str) -> tuple[Any, str]:
        """
        Read the content and path of a specified file using the storage adapter.

        Args:
            file_name (str): The name of the data configuration module file to be read.

        Returns:
            tuple[Any, str]: A tuple containing the content of the file and its complete path if read successfully.

        Raises:
            FileNotFoundError: If no valid file is found for the specified file name.
        """
        # Construct the complete path with the default data format
        complete_path = f"{self.FILE_PATH_PREFIX}{file_name}"
        # Check if the file exists using the storage adapter
        if self.storage_adapter.exists(complete_path):
            try:
                # Attempt to read the file content
                file_content = self.storage_adapter.read_file(complete_path)
                if file_content:
                    return file_content, complete_path
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
                file_name=file_name, directory_path=AppConfig.DEFAULT_DATA_PATH
            )
        )

    def _deserialize_content(self, file_name: str, file_content: Any) -> Any:
        """
        Deserialize the file content using the appropriate file format adapter.

        Args:
            file_name (str): The name of the data configuration module file.
            file_content (Any): The content of the file to be deserialized.

        Returns:
            Any: The deserialized content of the file.

        Raises:
            Exception: If there is an error deserializing the file content.
        """
        try:
            file_format_adapter = FileFormatFactory.get_adapter(file_name)
            deserialized_content = file_format_adapter.deserialize(file_content)

            # Check if the deserialized content is valid
            if not isinstance(deserialized_content, dict):
                raise ValueError

            return deserialized_content
        except Exception as e:
            logger.error(
                self.ERROR_DESERIALIZING_CONTENT.format(file_name=file_name, error=e)
            )
            raise

    def _set_data_prefix(self):
        """
        Set the default data configuration file path prefix.

        This function sets the `FILE_PATH_PREFIX` to the default data configuration path
        if the `PREFIX` attribute of the `storage_adapter` is `None`. This is typically
        used when the default storage adapter is in use, ensuring that data configurations
        are loaded from the correct default directory.
        """
        if self.storage_adapter.PREFIX is None:
            self.FILE_PATH_PREFIX = AppConfig.DEFAULT_TEST_CONFIGS_PATH + "/"
