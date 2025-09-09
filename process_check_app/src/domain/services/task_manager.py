import asyncio
import json
from datetime import datetime
from typing import Callable, Optional

from adapters.file_format.json_adapter import JsonAdapter
from adapters.storage_provider.local_storage_adapter import LocalStorageAdapter
from domain.entities.attack_module_entity import AttackModuleEntity
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.prompt_entity import PromptEntity
from domain.services.app_config import AppConfig
from domain.services.enums.file_types import FileTypes
from domain.services.enums.module_types import ModuleTypes
from domain.services.enums.test_types import TestTypes
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
    ) -> str:
        """
        Run a benchmark task with the specified parameters.

        Args:
            run_id (str): The unique identifier for the run.
            test_name (str): The name of the benchmark test.
            dataset (str): The name of the dataset module to be loaded.
            metric (str): The name of the metric module to be loaded.
            connector (str): The name of the connector configuration to be loaded.
            prompt_processor (str): The name of the prompt processor module to be loaded.
            callback_fn (Callable, optional): A callback function to be executed at various stages of the benchmark task
            Defaults to None.

        Returns:
            str: The file path where the results are stored.
        """
        try:
            # Record the start time of the benchmark
            start_time = datetime.now()
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

            # Get the connector configuration
            connector_entity = self._get_connector_config(connector)
            if connector_entity is None:
                return ""

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
            # Generate prompts from the dataset
            prompts = self._generate_prompts(dataset_entity)
            logger.info(self.INFO_PROMPTS_COUNT.format(count=len(prompts)))
            # Process the prompts and get results
            self.prompts_with_results, evaluation_summary = (
                await prompt_processor_instance[0].process_prompts(
                    prompts, connector_entity, metric, callback_fn
                )
            )

            # Invoke the callback function to indicate the formatting stage
            self._invoke_callback(callback_fn, stage=2, message="Formatting results")
            individual_results = self._convert_prompt_entities_to_dicts(
                self.prompts_with_results, metric
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
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Benchmark ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Benchmark duration: {duration} seconds")

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
        file_path = f"{AppConfig.DEFAULT_RESULTS_PATH}/{run_id}.json"
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
        """
        Convert a list of PromptEntity objects to a list of dictionaries.

        Args:
            prompt_entities (list[PromptEntity]): A list of PromptEntity instances to be converted.
            metric (dict): The metric configuration.

        Returns:
            list[dict]: A list of dictionaries representing the prompt entities.
        """

        # get the metric configuration from the config file
        try:
            _, metric_id = self._load_module(
                ModuleLoader,
                metric["name"],
                ModuleTypes.METRIC,
                self.METRIC_LOADED_MSG,
                self.ERROR_RETRIEVING_CONFIG_MSG,
            )
            app_config = AppConfig()
            metric_config = app_config.get_metric_config(metric_id)
            if metric_config is None:
                logger.error(self.METRIC_CONFIG_NOT_FOUND_MSG.format(metric_id))
                raise ValueError(self.METRIC_CONFIG_NOT_FOUND_MSG.format(metric_id))
        except Exception as e:
            logger.error(self.ERROR_RETRIEVING_CONFIG_MSG.format(metric_id, e))
            raise

        # if there is no need to categorise the results (i.e. results are continuous values and not discrete values)
        if not metric_config.params.get("categorise_result"):
            uncategorised_results = []
            for prompt_entity in prompt_entities:
                prompt_entity_dict = {
                    "prompt_id": prompt_entity.index,
                    "prompt": prompt_entity.evaluation_result.prompt,
                    "predicted_result": {
                        "response": prompt_entity.evaluation_result.predicted_result.response,
                        "context": prompt_entity.evaluation_result.predicted_result.context,
                    },
                    "target": prompt_entity.evaluation_result.target,
                    "evaluated_result": prompt_entity.evaluation_result.evaluated_result,
                    "prompt_additional_info": prompt_entity.additional_info,
                    "state": prompt_entity.state.value,
                }
                uncategorised_results.append(prompt_entity_dict)
            return {"all_results": uncategorised_results}
        else:
            # Original categorization logic for metrics that need categorization
            categorised_results = {}
            for prompt_entity in prompt_entities:
                evaluated_response = prompt_entity.evaluation_result.evaluated_result[
                    "evaluated_response"
                ]

                # Create a new list for this evaluated_response if it doesn't exist
                if evaluated_response not in categorised_results:
                    categorised_results[evaluated_response] = []

                prompt_entity_dict = {
                    "prompt_id": prompt_entity.index,
                    "prompt": prompt_entity.evaluation_result.prompt,
                    "predicted_result": {
                        "response": prompt_entity.evaluation_result.predicted_result.response,
                        "context": prompt_entity.evaluation_result.predicted_result.context,
                    },
                    "target": prompt_entity.evaluation_result.target,
                    "evaluated_result": prompt_entity.evaluation_result.evaluated_result,
                    "prompt_additional_info": prompt_entity.additional_info,
                    "state": prompt_entity.state.value,
                }

                # Append the prompt entity to the appropriate list
                categorised_results[evaluated_response].append(prompt_entity_dict)

            # Sort the dictionary by key
            categorised_results = {
                key: categorised_results[key] for key in sorted(categorised_results)
            }

            return categorised_results

    def _format_metadata(
        self,
        test_name: str,
        dataset: str,
        metric: dict,
        connector_entity: ConnectorEntity,
        task_type: str,
    ) -> dict:
        """
        Format the metadata for the benchmark results.

        Args:
            test_name (str): The name of the test that has been run.
            dataset (str): The name of the dataset module.
            metric (dict): The metric information in dictionary.
            connector_entity (ConnectorEntity): The connector entity configuration.
            task_type (str): The type of the task (e.g., "benchmark", "scan").

        Returns:
            dict: The formatted metadata.
        """
        formatted_metadata = {
            "test_name": test_name,
            "dataset": dataset,
            "metric": metric,
            "type": task_type,
            "connector": {
                "connector_adapter": connector_entity.connector_adapter,
                "model": connector_entity.model,
                "model_endpoint": connector_entity.model_endpoint,
                "params": connector_entity.params,
                "connector_pre_prompt": connector_entity.connector_pre_prompt,
                "connector_post_prompt": connector_entity.connector_post_prompt,
                "system_prompt": connector_entity.system_prompt,
            },
        }

        # Remove dataset for scan as we do not use dataset for our current attack modules
        if task_type == "scan":
            del formatted_metadata["dataset"]

        return formatted_metadata

    def _generate_prompts(self, dataset_entity: DatasetEntity) -> list[PromptEntity]:
        """
        Generate a list of PromptEntity instances from the dataset entity.

        Args:
            dataset_entity (DatasetEntity): The dataset entity containing examples.

        Returns:
            list[PromptEntity]: The list of generated PromptEntity instances.
        """
        logger.info(self.INFO_GENERATING_PROMPTS)
        return [
            PromptEntity(
                index=index,
                prompt=example.pop("input", ""),
                target=example.pop("target", ""),
                reference_context=example.pop("reference_context", ""),
                model_prediction=None,
                evaluation_result={},
                additional_info={key: value for key, value in example.items()},
            )
            for index, example in enumerate(dataset_entity.examples, 1)
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
