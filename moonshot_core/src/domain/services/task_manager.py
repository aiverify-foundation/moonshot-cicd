import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Callable, Optional

from adapters.file_format.json_adapter import JsonAdapter
from adapters.storage_provider.local_storage_adapter import LocalStorageAdapter
from domain.entities.attack_module_entity import AttackModuleEntity
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.prompt_entity import PromptEntity
from domain.services.app_config import AppConfig
from domain.services.dataset_examples_converter import examples_to_prompts
from domain.services.enums.file_types import FileTypes
from domain.services.enums.module_types import ModuleTypes
from domain.services.enums.task_manager_status import TaskManagerStatus
from domain.services.enums.test_types import TestTypes
from domain.services.ga_results_formatter import (
    convert_prompt_entities_to_dicts,
)
from domain.services.ga_results_formatter import format_metadata as format_ga_metadata
from domain.services.loader.file_loader import FileLoader
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class TaskManager:
    """
    TaskManager is responsible for managing and running various tasks such as benchmarks and red teaming.
    """

    # Define various log messages and error messages
    INFO_PROMPTS_COUNT = "[TaskManager] Number of prompts generated: {count}"
    LOADING_MODULES_MSG = (
        "[TaskManager] Loading the specified components. Please wait..."
    )
    DATASET_LOADED_MSG = "[TaskManager] Dataset module loaded successfully."
    TEST_CONFIG_LOADED_MSG = "[TaskManager] Test Config module loaded successfully."
    TEST_CONFIG_MISSING_ERROR = "[TaskManager] {test_name} does not exist."
    PROMPT_PROCESSOR_LOADED_MSG = (
        "[TaskManager] Prompt processor module loaded successfully."
    )
    ERROR_LOADING_DATASET = "[TaskManager] Error loading the dataset module: {error}"
    ERROR_LOADING_TEST_CONFIG = (
        "[TaskManager] Error loading the test config module: {error}"
    )
    ERROR_LOADING_PROMPT_PROCESSOR = (
        "[TaskManager] Error loading the prompt processor module: {error}"
    )
    ERROR_PROCESSING_BENCHMARK = (
        "[TaskManager] Error occured when running benchmark: {error}"
    )
    PROCESSING_BENCHMARK_MSG = (
        "[TaskManager] Processing benchmark {test_name} with run ID {run_id}"
    )
    PROCESSING_SCAN_MSG = (
        "[TaskManager] Processing scan {test_name} with run ID {run_id}"
    )
    ATTACK_MODULE_LOADED_MSG = "[TaskManager] Attack module loaded successfully."
    ERROR_LOADING_ATTACK_MODULE = (
        "[TaskManager] Error loading the attack module: {error}"
    )
    ERROR_FORMATTING_RESULTS = "[TaskManager] Error formatting the results: {error}"
    ERROR_EMPTY_FORMATTED_RESULTS = (
        "[TaskManager] Formatted results are empty. Unable to write to file."
    )
    ERROR_WRITING_RESULTS = "[TaskManager] Error writing formatted results: {error}"
    SUCCESSFUL_WRITING_OF_RESULTS = "[TaskManager] Results written to {file_path}."
    INFO_GENERATING_PROMPTS = "[TaskManager] Generating prompts from dataset."
    ERROR_SERIALIZING_RESULTS = "[TaskManager] Error serializing the results: {error}"
    ERROR_LOADING_CONNECTOR_CONFIG = "[TaskManager] Error loading the connector configuration: {connector_configuration}"  # noqa: E501

    METRIC_CONFIG_NOT_FOUND_MSG = "[TaskManager] Metric config not found for {}"
    METRIC_LOADED_MSG = "[TaskManager] Metric Config Loaded Successfully"
    ERROR_RETRIEVING_CONFIG_MSG = (
        "[TaskManager] Error retrieving metric config for {}: {}"
    )

    async def run_benchmark(
        self,
        run_id: str,
        test_name: str,
        dataset: str,
        metric: dict,
        connector: str,
        prompt_processor: str,
        callback_fn: Callable | None = None,
        write_result: bool = True,
        write_to_db: bool = False,
        db_run_id: Optional[int] = None,
        test_id: Optional[int] = None,
        connector_entity: Optional[ConnectorEntity] = None,
    ) -> str:
        """
        Run a benchmark task with the specified parameters.

        Args:
            run_id (str): The unique identifier for the run (logging, file paths).
            test_name (str): The name of the benchmark test.
            dataset (str): The name of the dataset module to be loaded.
            metric (str): The name of the metric module to be loaded.
            connector (str): YAML connector id when connector_entity is None.
            prompt_processor (str): The name of the prompt processor module to be loaded.
            callback_fn (Callable, optional): A callback function to be executed at various stages of the benchmark task
            Defaults to None.
            db_run_id (int, optional): DB benchmark_run.id when writing to DB; if None, DB write is skipped.
            test_id (int, optional): DB benchmark_test.id for run_test_status; if None, a default is used (TODO: proper resolution).
            connector_entity (Optional[ConnectorEntity]): When set, used instead of YAML connector lookup.

        Returns:
            str: The file path where the results are stored.
        """
        try:
            # Record the start time of the benchmark (UTC; matches benchmark_run.start_time and API contract)
            start_time = datetime.now(timezone.utc)

            logger.info(
                f"Benchmark started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Log the start of benchmark processing
            logger.info(
                self.PROCESSING_BENCHMARK_MSG.format(test_name=test_name, run_id=run_id)
            )

            # Invoke the callback function to indicate the loading stage
            self._invoke_callback(callback_fn, stage=0, message="Loading modules")
            logger.info(self.LOADING_MODULES_MSG)

            # Get the connector configuration (DB-built entity or YAML id)
            if connector_entity is not None:
                resolved_connector = connector_entity
            else:
                resolved_connector = self._get_connector_config(connector)
            if resolved_connector is None:
                return ""
            connector_entity = resolved_connector

            # Load the dataset and prompt processor modules
            dataset_entity, prompt_processor_instance = (
                self._load_module(
                    FileLoader,
                    dataset,
                    FileTypes.DATASET,
                    self.DATASET_LOADED_MSG,
                    self.ERROR_LOADING_DATASET,
                ),
                self._load_module(
                    ModuleLoader,
                    prompt_processor,
                    ModuleTypes.PROMPT_PROCESSOR,
                    self.PROMPT_PROCESSOR_LOADED_MSG,
                    self.ERROR_LOADING_PROMPT_PROCESSOR,
                ),
            )
            if not dataset_entity or not prompt_processor_instance:
                return ""

            # Invoke the callback function to indicate the running stage
            self._invoke_callback(callback_fn, stage=1, message="Running benchmark")
            saved_benchmark_run_test_status = None
            if write_to_db:
                if db_run_id is None:
                    logger.info(
                        "[TaskManager] Skipping DB write: no run_id provided "
                        "(use start_benchmark_run or pass db_run_id for persistence). "
                        "run_id=%s test_name=%s",
                        run_id,
                        test_name,
                    )
                else:
                    # TODO: proper default_test_id resolution (e.g. resolve from benchmark_test by test_name)
                    effective_test_id = test_id if test_id is not None else 1
                    from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (  # noqa: WPS433
                        SqlAlchemyBenchmarkRunTestStatusRepository,
                    )
                    from application.services.benchmark_run_test_status_service import (  # noqa: WPS433
                        BenchmarkRunTestStatusService,
                    )
                    from domain.entities.benchmark_run_test_status_entity import (  # noqa: WPS433
                        BenchmarkRunTestStatusEntity,
                    )

                    status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
                    existing_status = status_repo.get_by_run_and_test(
                        db_run_id, effective_test_id
                    )
                    if (
                        existing_status is not None
                        and existing_status.status == "not_started"
                    ):
                        saved_benchmark_run_test_status = existing_status
                        saved_benchmark_run_test_status.status = "in_progress"
                        saved_benchmark_run_test_status.start_dt = start_time
                        BenchmarkRunTestStatusService().update_run_test_status(
                            saved_benchmark_run_test_status
                        )
                    # else throw error

            # Generate prompts: from DB run_test_prompts when write_to_db and run_test exists, else from dataset
            run_test_id = getattr(saved_benchmark_run_test_status, "id", None)
            if write_to_db and run_test_id is not None:
                prompts = self._generate_prompts_from_run_test_id(run_test_id)
            else:
                prompts = self._generate_prompts(dataset_entity)
            logger.info(self.INFO_PROMPTS_COUNT.format(count=len(prompts)))
            # Process the prompts and get results
            prompts_with_results, evaluation_summary = await prompt_processor_instance[
                0
            ].process_prompts(
                prompts,
                connector_entity,
                metric,
                callback_fn,
                write_to_db,
                run_test_id=run_test_id,
            )

            # Invoke the callback function to indicate the formatting stage
            self._invoke_callback(callback_fn, stage=2, message="Formatting results")
            individual_results = self._convert_prompt_entities_to_dicts(
                prompts_with_results, metric
            )
            # Format the metadata for the benchmark results
            metadata = self._format_metadata(
                test_name, dataset, metric, connector_entity, "benchmark"
            )
            benchmark_results = {
                "metadata": metadata,
                "results": {
                    "individual_results": individual_results,
                    "evaluation_summary": evaluation_summary,
                },
            }

            # Record the end time of the benchmark and calculate the duration
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Benchmark ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Benchmark duration: {duration} seconds")

            if write_to_db and saved_benchmark_run_test_status is not None:
                saved_benchmark_run_test_status.end_dt = end_time
                has_errors = any(
                    p.state == TaskManagerStatus.ERROR for p in prompts_with_results
                )
                saved_benchmark_run_test_status.status = (
                    "completed_with_errors" if has_errors else "completed"
                )
                from application.services.benchmark_run_test_status_service import (  # noqa: WPS433
                    BenchmarkRunTestStatusService,
                )

                BenchmarkRunTestStatusService().update_run_test_status(
                    saved_benchmark_run_test_status
                )

            # Update the metadata with timing information
            benchmark_results["metadata"].update(
                {
                    "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration": duration,
                }
            )

            # Invoke the callback function to indicate the writing stage
            self._invoke_callback(callback_fn, stage=3, message="Writing results")
            # Serialize the results to JSON
            serialized_results = self._serialize_results(benchmark_results)
            if not serialized_results:
                return ""

            # Write result to a file if true. Else return the value of the run.
            if write_result:
                # Store the results to a local path and return the file path
                return self._store_results_to_local_path(run_id, serialized_results)
            else:
                return serialized_results
        except Exception as e:
            logger.error(self.ERROR_PROCESSING_BENCHMARK.format(error=e))
            raise (e)

    async def run_scan(
        self,
        run_id: str,
        test_name: str,
        attack_module: dict,
        metric: dict,
        connector: str,
        dataset: str = "",
        prompt: str = "",
        prompt_processor: str = "asyncio_prompt_processor_adapter",
        callback_fn: Callable | None = None,
        write_result: bool = True,
    ) -> str:
        """
        Execute a red teaming operation using the specified attack module, metric, and connector.

        Args:
            run_id (str): The unique identifier for the run.
            test_name (str): The name of the scan test.
            attack_module (str): The name of the attack module to be loaded.
            metric (str): The name of the metric module to be loaded.
            connector (str): The name of the connector configuration to be loaded.
            dataset (str, optional): The name of the dataset module to be loaded. Defaults to an empty string.
            prompt (str, optional): The seed prompt for the red teaming. Defaults to an empty string.
            prompt_processor (str, optional): The name of the prompt processor module to be used.
            Defaults to "asyncio_prompt_processor_adapter".
            callback_fn (Callable, optional): A callback function to update the progress of the scan test.
            Defaults to None.

        Returns:
            str: The file path where the results are stored.
        """
        # Record the start time of the scan
        start_time = datetime.now()
        logger.info(f"Scan started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Log the start of scan processing
        logger.info(self.PROCESSING_SCAN_MSG.format(test_name=test_name, run_id=run_id))

        # Invoke the callback function to indicate the loading stage
        self._invoke_callback(callback_fn, stage=0, message="Loading modules")
        logger.info(self.LOADING_MODULES_MSG)

        # Create an AttackModuleEntity with the provided parameters
        am_entity = AttackModuleEntity(
            connector=connector,
            metric=metric,
            dataset=dataset,
            prompt=prompt,
            prompt_processor=prompt_processor,
            callback_fn=callback_fn,
        )
        try:
            # Load the attack module
            am_inst, am_id = self._load_module(
                ModuleLoader,
                attack_module["name"],
                ModuleTypes.ATTACK_MODULE,
                self.ATTACK_MODULE_LOADED_MSG,
                self.ERROR_LOADING_ATTACK_MODULE,
            )
        except Exception as e:
            raise (e)

        # Configure the attack module instance
        am_inst.configure(am_id=am_id, am_entity=am_entity)
        am_inst.update_params(attack_module["params"])
        # Invoke the callback function to indicate the scan stage
        self._invoke_callback(callback_fn, stage=1, message="Performing scan")
        eval_results, evaluation_summary = await am_inst.execute()

        # Invoke the callback function to indicate the formatting stage
        self._invoke_callback(callback_fn, stage=2, message="Formatting results")

        # Get the connector configuration
        connector_entity = self._get_connector_config(connector)
        if connector_entity is None:
            return ""
        # Convert the evaluation results to a list of dictionaries
        individual_results = self._convert_prompt_entities_to_dicts(
            eval_results, metric
        )
        metadata = self._format_metadata(
            test_name, dataset, metric, connector_entity, "scan"
        )
        metadata["attack_module"] = attack_module
        scan_results = {
            "metadata": metadata,
            "results": {
                "individual_results": individual_results,
                "evaluation_summary": evaluation_summary,
            },
        }

        # Record the end time of the scan and calculate the duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Scan ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Scan duration: {duration} seconds")

        # Update the metadata with timing information
        scan_results["metadata"].update(
            {
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration,
            }
        )

        # Invoke the callback function to indicate the writing stage
        self._invoke_callback(callback_fn, stage=3, message="Writing results")
        # Serialize the results to JSON
        serialized_results = self._serialize_results(scan_results)
        if not serialized_results:
            return ""

        # Write result to a file if true. Else return the value of the run.
        if write_result:
            # Store the results to a local path and return the file path
            return self._store_results_to_local_path(run_id, serialized_results)
        else:
            return serialized_results

    async def run_test(
        self,
        run_id: str,
        test_config_id: str,
        connector_configuration: str,
        prompt_processor: str = "asyncio_prompt_processor_adapter",
        callback_fn: Callable | None = None,
        write_result: bool = True,
    ) -> str:
        """
        Execute a test run based on the provided configuration file and parameters.

        This asynchronous method processes each test defined in the configuration file,
        running either a benchmark or a scan depending on the test's specifications.

        Args:
            run_id (str): The unique identifier for the test run.
            test_config_id (str): The id of the test configuration to run.
            connector_configuration (str): The connector configuration to be used for the test.
            prompt_processor (str, optional): The prompt processor to be used. Defaults to
            "asyncio_prompt_processor_adapter".
            callback_fn (Callable, optional): A callback function to be executed at various stages of the test.
            Defaults to None.
            write_result (bool, optional): Flag indicating whether to write the results to a file. Defaults to True.

        Returns:
            str: The file path where the results are stored if write_result is True, otherwise the serialized results.
        """
        test_config_file_name = AppConfig().get_test_config_file_path()
        test_config_inst = self._load_module(
            FileLoader,
            test_config_file_name,
            FileTypes.TEST_CONFIG,
            self.TEST_CONFIG_LOADED_MSG,
            self.ERROR_LOADING_TEST_CONFIG,
        )

        if not test_config_inst:
            return ""
        # Record the start time of the scan
        start_time = datetime.now()
        logger.info(
            f"Test configuration started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        tests = test_config_inst.get(test_config_id)
        if tests is None:
            logger.error(
                self.TEST_CONFIG_MISSING_ERROR.format(test_name=test_config_id)
            )
            raise ValueError(
                f"{self.TEST_CONFIG_MISSING_ERROR.format(test_name=test_config_id)}"
            )

        tasks = []
        for test in tests:
            if test.type is TestTypes.BENCHMARK:
                # Run benchmark
                task = self.run_benchmark(
                    run_id=run_id,
                    test_name=test.name,
                    dataset=test.dataset,
                    metric=test.metric,
                    connector=connector_configuration,
                    prompt_processor=prompt_processor,
                    callback_fn=callback_fn,
                    write_result=False,
                )
            elif test.type is TestTypes.SCAN:
                # Run scan
                task = self.run_scan(
                    run_id=run_id,
                    test_name=test.name,
                    attack_module=test.attack_module,
                    metric=test.metric,
                    connector=connector_configuration,
                    dataset=test.dataset,
                    prompt=test.prompt,
                    prompt_processor=prompt_processor,
                    callback_fn=callback_fn,
                    write_result=False,
                )
            else:
                logger.error(
                    self.ERROR_LOADING_TEST_CONFIG.format(
                        error=f"Invalid test type:{test.type}"
                    )
                )
                raise RuntimeError(self.ERROR_LOADING_TEST_CONFIG)
            tasks.append(task)

        # Invoke the callback function to indicate the stage of running test config
        self._invoke_callback(
            callback_fn, stage=1, message="Running test configuration"
        )
        eval_results = await asyncio.gather(*tasks)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(
            f"Test configuration ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info(f"Test configuration duration: {duration} seconds")

        run_metadata = {
            "run_metadata": {
                "run_id": run_id,
                "test_id": test_config_id,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration,
            }
        }
        json_results = [json.loads(result) for result in eval_results]

        formatted_json_results = {"run_results": json_results}

        final_results = run_metadata | formatted_json_results
        final_results_str = json.dumps(final_results, indent=4)

        # Write result to a file if true. Else return the value of the run.
        if write_result:
            # Store the results to a local path and return the file path
            return self._store_results_to_local_path(run_id, final_results_str)
        else:
            return final_results_str

    def _store_results_to_local_path(
        self, run_id: str, formatted_result_json: str
    ) -> str:
        """
        Store the results to a local path.

        Args:
            run_id (str): The unique identifier for the run.
            formatted_result_json (str): The formatted results in JSON format.

        Returns:
            str: The file path where the results are stored.
        """
        # Initialize the local storage adapter
        local_adapter = LocalStorageAdapter()
        # Define the file path for storing the results
        results_dir = os.environ.get(
            "MOONSHOT_BENCHMARK_RESULTS_DIR", AppConfig.DEFAULT_RESULTS_PATH
        )
        file_path = f"{results_dir}/{run_id}.json"
        try:
            # Write the results to the file
            success, message = local_adapter.write_file(
                file_path, formatted_result_json
            )
            if success:
                logger.info(
                    self.SUCCESSFUL_WRITING_OF_RESULTS.format(file_path=file_path)
                )
                return file_path
            else:
                logger.error(self.ERROR_WRITING_RESULTS.format(error=message))
                return ""
        except Exception as e:
            logger.error(self.ERROR_WRITING_RESULTS.format(error=str(e)))
            return ""

    def _convert_prompt_entities_to_dicts(
        self, prompt_entities: list[PromptEntity], metric: dict
    ) -> dict:
        """Delegate to shared GA Schema1 formatter."""
        return convert_prompt_entities_to_dicts(prompt_entities, metric)

    def _format_metadata(
        self,
        test_name: str,
        dataset: str,
        metric: dict,
        connector_entity: ConnectorEntity,
        task_type: str,
    ) -> dict:
        """Delegate to shared GA Schema1 formatter."""
        return format_ga_metadata(
            test_name, dataset, metric, connector_entity, task_type
        )

    def _generate_prompts_from_run_test_id(
        self, run_test_id: int
    ) -> list[PromptEntity]:
        """
        Generate a list of PromptEntity instances from seeded benchmark_run_test_prompt rows.

        Used when write_to_db is True and a run_test_status exists, so prompts already have
        benchmark_run_test_prompt_id set for id-based updates.

        Args:
            run_test_id: The benchmark_run_test_status.id to load run test prompts for.

        Returns:
            list[PromptEntity]: The list of prompt entities with benchmark_run_test_prompt_id set.
        """
        from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import (  # noqa: WPS433
            SqlAlchemyBenchmarkRunTestPromptRepository,
        )

        logger.info(self.INFO_GENERATING_PROMPTS)
        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        run_test_prompts = repo.get_all_by_run_test_id(run_test_id)
        return [
            PromptEntity(
                index=index,
                prompt=entity.prompt_additional_info or "",
                target=entity.target or "",
                reference_context="",
                model_prediction=None,
                evaluation_result={},
                additional_info={},
                benchmark_run_test_prompt_id=entity.id,
            )
            for index, entity in enumerate(run_test_prompts, 1)
        ]

    def _generate_prompts(self, dataset_entity: DatasetEntity) -> list[PromptEntity]:
        """
        Generate a list of PromptEntity instances from the dataset entity.

        Args:
            dataset_entity (DatasetEntity): The dataset entity containing examples.

        Returns:
            list[PromptEntity]: The list of generated PromptEntity instances.
        """
        logger.info(self.INFO_GENERATING_PROMPTS)
        prompt_entities = examples_to_prompts(dataset_entity.examples or [])
        return [
            PromptEntity(
                index=index,
                prompt=p.prompt,
                target=p.target,
                reference_context="",
                model_prediction=None,
                evaluation_result={},
                additional_info={},
            )
            for index, p in enumerate(prompt_entities, 1)
        ]

    def _serialize_results(self, results: dict) -> Optional[str]:
        """
        Serialize the results to JSON.

        Args:
            results (dict): The results to be serialized.

        Returns:
            Optional[str]: The serialized results in JSON format, or None if serialization fails.
        """
        try:
            # Initialize the JSON adapter
            json_adapter = JsonAdapter()
            # Serialize the results to JSON
            return json_adapter.serialize(results)
        except Exception as e:
            logger.error(self.ERROR_SERIALIZING_RESULTS.format(error=str(e)))
            return None

    def _load_module(
        self, loader, module_name: str, module_type, success_msg: str, error_msg: str
    ):
        """
        Load a module using the specified loader.

        Args:
            loader: The loader to use for loading the module.
            module_name (str): The name of the module to be loaded.
            module_type: The type of the module to be loaded.
            success_msg (str): The success message to log.
            error_msg (str): The error message to log in case of failure.

        Returns:
            The loaded module instance, or None if loading fails.
        """
        try:
            # Load the module using the provided loader
            module_instance = loader.load(module_name, module_type)
            logger.info(success_msg)
            return module_instance
        except Exception as e:
            logger.error(error_msg.format(error=str(e)))
            raise e

    def _invoke_callback(
        self, callback_fn: Optional[Callable], stage: int, message: str
    ):
        """
        Invoke the callback function if it is provided.

        Args:
            callback_fn (Optional[Callable]): The callback function to invoke.
            stage (int): The current stage of the process.
            message (str): The message to pass to the callback function.
        """
        if callback_fn:
            callback_fn(stage=stage, message=message)

    def _get_connector_config(self, connector: str) -> Optional[ConnectorEntity]:
        """
        Get the connector configuration.

        Args:
            connector (str): The name of the connector configuration to be loaded.

        Returns:
            Optional[ConnectorEntity]: The connector configuration entity, or None if loading fails.
        """
        connector_config = AppConfig().get_connector_config(connector)
        if connector_config is None:
            logger.error(
                self.ERROR_LOADING_CONNECTOR_CONFIG.format(
                    connector_configuration=connector
                )
            )
            return None
        return connector_config
