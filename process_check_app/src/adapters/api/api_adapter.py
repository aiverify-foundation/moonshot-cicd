import os
import shutil
from typing import Callable

from domain.ports.api_port import ApiPort
from domain.services.app_config import AppConfig
from domain.services.loader.factory.storage_provider_factory import (
    StorageProviderFactory,
)
from domain.services.logger import configure_logger
from domain.services.task_manager import TaskManager

# Create a logger for this module
logger = configure_logger(__name__)


class ApiAdapter(ApiPort):
    """
    Adapter for API interactions.

    This class provides methods to create and run various tests, including benchmark tests,
    scan tests, and run tests based on configuration files.
    """

    # Logging messages for benchmark tests
    BENCHMARK_INFO_MSG = (
        "[ApiAdapter] Creating a new benchmark test with run_id: {run_id}, dataset_id: {dataset_id}, "
        "metric_id: {metric_id}, and connector_configuration: {connector_configuration}"
    )
    CONNECTOR_CONFIG_NOT_FOUND_MSG = (
        "[ApiAdapter] Connector configuration '{connector_configuration}' not found"
    )
    BENCHMARK_SUCCESS_MSG = (
        "[ApiAdapter] Benchmark test successfully created with run_id: {run_id}"
    )
    BENCHMARK_ERROR_MSG = (
        "[ApiAdapter] An error occurred while creating the benchmark test: {error}"
    )

    # Logging messages for scan tests
    SCAN_INFO_MSG = (
        "[ApiAdapter] Creating a new scan test with run_id: {run_id}, attack_module: {attack_module}, "
        "metric: {metric} and connector_configuration: {connector_configuration}"
    )
    SCAN_SUCCESS_MSG = (
        "[ApiAdapter] Scan test successfully created with run_id: {run_id}"
    )
    SCAN_ERROR_MSG = (
        "[ApiAdapter] An error occurred while creating the scan test: {error}"
    )

    TEST_CONFIG_SUCCESS_MSG = "[ApiAdapter] Test config tests have been completed. Successfully created with run_id: {run_id}"  # noqa: E501
    RUN_TEST_ERROR_MSG = (
        "[ApiAdapter] An error occurred while creating the config test: {error}"
    )
    # Logging message for file exist errors
    FILE_EXIST_ERROR = "[ApiAdapter] A file with the run_id '{run_id}' already exists in the results directory."

    def __init__(self):
        # Get the configuration
        self.app_config = AppConfig()

    async def create_run_test(
        self,
        run_id: str,
        test_config_id: str,
        connector_configuration: str,
        prompt_processor: str = "asyncio_prompt_processor_adapter",
        callback_fn: Callable | None = None,
    ) -> None:
        """
        Asynchronously create and execute a run test.

        This method sets up and runs a test based on the provided configuration file
        and other parameters.

        Args:
            run_id (str): The unique identifier for the test run.
            test_config_id (str): The id of the test config to run.
            connector_configuration (str): The connector configuration used for the test.
            prompt_processor (str, optional): The prompt processor to be used. Defaults to
            "asyncio_prompt_processor_adapter".
            callback_fn (Callable, optional): A callback function to update the progress of the test. Defaults to None.

        Returns:
            None
        """
        try:
            if self._check_run_id_exist(run_id):
                raise FileExistsError

            task_manager = TaskManager()
            await task_manager.run_test(
                run_id,
                test_config_id,
                connector_configuration,
                prompt_processor,
                callback_fn,
            )

            logger.info(self.TEST_CONFIG_SUCCESS_MSG.format(run_id=run_id))
        except FileExistsError:
            logger.error(self.FILE_EXIST_ERROR.format(run_id=run_id))
        except Exception as e:
            logger.error(self.RUN_TEST_ERROR_MSG.format(error=e))
        finally:
            self.delete_all_in_temp_folder()

    def delete_all_in_temp_folder(self) -> None:
        """
        Delete all contents within the default temporary folder.

        This function removes all files and subdirectories within the default temporary folder
        specified by AppConfig.DEFAULT_TEMP_PATH. It does not delete the folder itself.

        Returns:
            None

        Raises:
            FileNotFoundError: If the specified folder does not exist.
            PermissionError: If the operation lacks the necessary permissions.
            OSError: For other errors related to file operations.
        """
        folder_path = AppConfig.DEFAULT_TEMP_PATH

        if not os.path.exists(folder_path):
            return

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                raise OSError(f"Failed to delete {file_path}. Reason: {e}")

    def _check_run_id_exist(self, run_id: str) -> bool:
        """
        Check if the given run_id exists in any JSON file in the default results path.

        Args:
            run_id (str): The run_id to check for existence.

        Returns:
            bool: True if the run_id exists, False otherwise.
        """
        file_path = f"{self.app_config.DEFAULT_RESULTS_PATH}/{run_id}.json"

        storage_adapter = StorageProviderFactory.get_adapter(file_path)
        return storage_adapter.exists(file_path)
