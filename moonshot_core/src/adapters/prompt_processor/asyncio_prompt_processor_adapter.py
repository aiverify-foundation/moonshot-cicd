import asyncio
from datetime import datetime
from typing import Callable

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.model_config_entity import ModelConfigEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.prompt_entity import PromptEntity
from domain.ports.connector_port import ConnectorPort
from domain.ports.metric_port import MetricPort
from domain.ports.prompt_processor_port import PromptProcessorPort
from domain.services.app_config import AppConfig
from domain.services.enums.module_types import ModuleTypes
from domain.services.enums.task_manager_status import TaskManagerStatus
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

# This is required code for POC but it should be removed in the future.
from application.ports.model_config_repository import ModelConfigRepository
from application.services.sqlite_model_config_repository import SQLiteModelConfigRepository
from application.services.sqlite_adapter import SQLiteAdapter

# Initialize a logger for this module
logger = configure_logger(__name__)


class AsyncioPromptProcessor(PromptProcessorPort):

    def __init__(self):
        # Get the configuration
        self.app_config = AppConfig()

    """
    AsyncioPromptProcessor is responsible for processing prompts asynchronously
    using connector and metric instances.
    """

    CONNECTOR_LOADED_MSG = (
        "[AsyncioPromptProcessor] Connector module loaded successfully."
    )
    METRIC_LOADED_MSG = "[AsyncioPromptProcessor] Metric module loaded successfully."
    ERROR_LOADING_CONNECTOR = (
        "[AsyncioPromptProcessor] Failed to load the connector module."
    )
    ERROR_LOADING_METRIC = "[AsyncioPromptProcessor] Failed to load the metric module."
    ERROR_PROCESSING_PROMPT = "[AsyncioPromptProcessor] Failed to process prompt."

    async def process_single_prompt(
        self,
        prompt_entity: PromptEntity,
        connector_instance: ConnectorPort,
        metric_instance: MetricPort,
        write_to_db: bool = False,
        model_config_repository: ModelConfigRepository | None = None,
        run_id: int | None = None,
    ) -> PromptEntity:
        """
        Asynchronously process a single prompt entity using the provided connector and metric instances.

        Args:
            prompt_entity (PromptEntity): The prompt entity to be processed.
            connector_instance (ConnectorPort): The connector instance to process the prompt.
            metric_instance (MetricPort): The metric instance to evaluate the processed prompt.
            write_to_db (bool): Whether to write results to the database.
            model_config_repository (ModelConfigRepository | None): Optional repository for database operations.
                If write_to_db is True and this is None, database writes will be skipped with a warning.
            run_id (int | None): Optional. When provided and write_to_db is True, used as run_test_id to persist
                a benchmark_run_test_prompt row (benchmark run passes this when it wants to handle persistence).

        Returns:
            PromptEntity: The updated prompt entity with model predictions and evaluation results.
        """
        try:
            # Process the prompt using the connector instance
            processed_prompt = await connector_instance.get_response(
                prompt_entity.prompt
            )
            prompt_entity.model_prediction = processed_prompt
            reference_context = prompt_entity.reference_context

            # Evaluate the processed prompt using the metric instance
            metric_entity = MetricIndividualEntity(
                prompt=prompt_entity.prompt,
                predicted_result=prompt_entity.model_prediction,
                target=prompt_entity.target,
                reference_context=reference_context,
            )

            evaluated_result = await metric_instance.get_individual_result(
                metric_entity
            )

            metric_entity.evaluated_result = evaluated_result
            prompt_entity.evaluation_result = metric_entity

            if write_to_db and model_config_repository is not None:
                # Create a dummy model config
                # Use unique ID as name to avoid conflicts when multiple prompts write simultaneously
                unique_id = f"dummy_config1_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                dummy_model_config = ModelConfigEntity(
                    id=unique_id,
                    name=unique_id,  # Use unique ID as name to prevent overwrites
                    modelname="dummy-model",
                    providerID="1",
                    savedConfigPairs={"param1": "value1", "param2": "value2"},
                    lastUpdated=datetime.now()
                )
                
                # Save the model config using the repository
                try:
                    saved_config = model_config_repository.add_model_config(dummy_model_config)
                except Exception as db_error:
                    logger.error(
                        f"[AsyncioPromptProcessor] Failed to save model config to database: {db_error}",
                        exc_info=True
                    )
                    # Continue processing even if database write fails
                

            # When write_to_db and run_id: only update existing rows when prompt has benchmark_run_test_prompt_id (done in process_prompts after return). Do not insert.

            # Set the prompt entity state to completed
            prompt_entity.state = TaskManagerStatus.COMPLETED
        except Exception as e:
            # Set the prompt entity state to error and log the exception
            prompt_entity.state = TaskManagerStatus.ERROR
            logger.error(f"{self.ERROR_PROCESSING_PROMPT} {e}")
            raise (e)

        return prompt_entity

    async def process_prompts(
        self,
        prompts: list[PromptEntity],
        connector_entity: ConnectorEntity,
        metric: dict,
        callback_fn: Callable | None = None,
        write_to_db: bool = False,
        run_id: int | None = None,
    ) -> tuple[list[PromptEntity], dict]:
        """
        Asynchronously process a list of prompt entities concurrently using the specified connector and metric modules.

        Args:
            prompts (list[PromptEntity]): The list of prompt entities to be processed.
            connector_entity (ConnectorEntity): The connector entity configuration.
            metric (str): The name of the metric module to be loaded.
            callback_fn (Callable | None): The callback function to update the progress.
            write_to_db (bool): Whether to write results to the database.
            run_id (int | None): Optional. When provided and write_to_db is True, passed to each prompt as run_test_id
                for persisting benchmark_run_test_prompt rows (e.g. from benchmark run execution service).

        Returns:
            tuple[list[PromptEntity], dict]: A tuple containing the list of processed prompt entities with model
            predictions and evaluation results, and the evaluation summary.
        """
        # Use asyncio.gather to process all prompts concurrently
        # Initialize database adapter and repository once if write_to_db is True
        model_config_repository: ModelConfigRepository | None = None
        if write_to_db:
            sqlite_adapter = SQLiteAdapter()
            model_config_repository = SQLiteModelConfigRepository(sqlite_adapter)

        # Load existing run_test_prompts by run_test_id when write_to_db and run_id (for id-based update only)
        existing_run_test_prompts: list = []
        prompt_repo = None
        if write_to_db and run_id is not None:
            try:
                from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import (
                    SqlAlchemyBenchmarkRunTestPromptRepository,
                )
                prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
                existing_run_test_prompts = prompt_repo.get_all_by_run_test_id(run_id)
            except Exception as db_error:
                logger.error(
                    "[AsyncioPromptProcessor] Failed to load run test prompts for run_test_id=%s: %s",
                    run_id,
                    db_error,
                    exc_info=True,
                )

        try:
            # Load and configure the connector instance
            connector_instance, _ = ModuleLoader.load(
                connector_entity.connector_adapter, ModuleTypes.CONNECTOR
            )
            connector_instance.configure(connector_entity)
        except Exception as e:
            logger.error(f"{self.ERROR_LOADING_CONNECTOR} {e}")
            raise (e)

        try:
            # Load the metric instance
            metric_instance, met_id = ModuleLoader.load(
                metric["name"], ModuleTypes.METRIC
            )
            # Update the metric instance with the params from the metric config
            app_config = AppConfig()
            metric_config = app_config.get_metric_config(met_id)
            metric_instance.update_metric_params(metric_config.params)
        except Exception as e:
            logger.error(f"{self.ERROR_LOADING_METRIC} {e}")
            raise (e)

        # Retrieve max_concurrency from connector params or use defaults
        max_concurrency = connector_entity.params.get(
            "max_concurrency", self.app_config.get_common_config("max_concurrency")
        )

        # Test max_concurrency constraints
        if not isinstance(max_concurrency, int):
            raise TypeError("max_concurrency must be of type int.")
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1.")

        completed_count = 0
        # Create a semaphore to limit the number of concurrent tasks
        semaphore = asyncio.Semaphore(max_concurrency)

        async def process_and_count(
            prompt: PromptEntity, index: int, run_id: int | None = None
        ) -> PromptEntity:
            """
            Asynchronously process a single prompt entity and update the completion count.

            Args:
                prompt (PromptEntity): The prompt entity to be processed.
                index (int): The index of the prompt in the list.
                run_id (int | None): Optional run_test_id for persisting benchmark_run_test_prompt when write_to_db.

            Returns:
                PromptEntity: The processed prompt entity with updated state and results.
            """
            # Use nonlocal to modify the completed_count variable from the enclosing scope
            nonlocal completed_count

            # Send the prompt and update on the current status of the prompts, and return the result
            async with semaphore:
                prompt.state = TaskManagerStatus.RUNNING
                if callback_fn:
                    callback_fn(
                        prompt.state.name.lower(), len(prompts), completed_count, index
                    )

                result = await self.process_single_prompt(
                    prompt,
                    connector_instance,
                    metric_instance,
                    write_to_db,
                    model_config_repository,
                    run_id=run_id,
                )
                completed_count += 1

                # Update existing benchmark_run_test_prompt row by id when set (no insert)
                if (
                    write_to_db
                    and run_id is not None
                    and prompt_repo is not None
                    and result.benchmark_run_test_prompt_id is not None
                ):
                    try:
                        entity = next(
                            (
                                e
                                for e in existing_run_test_prompts
                                if e.id == result.benchmark_run_test_prompt_id
                            ),
                            None,
                        )
                        if entity is not None:
                            if hasattr(result.model_prediction, "response"):
                                entity.prediction_result = result.model_prediction.response
                            else:
                                entity.prediction_result = (
                                    str(result.model_prediction)
                                    if result.model_prediction is not None
                                    else None
                                )
                            metric_entity = result.evaluation_result
                            evaluated = (
                                metric_entity.evaluated_result
                                if metric_entity else None
                            )
                            entity.evaluation_prediction_result = (
                                str(evaluated) if evaluated is not None else None
                            )
                            entity.evaluation_accuracy = (
                                float(evaluated)
                                if isinstance(evaluated, (int, float))
                                else None
                            )
                            entity.status = result.state.name.lower()
                            prompt_repo.update(entity)
                    except Exception as db_error:
                        logger.error(
                            "[AsyncioPromptProcessor] Failed to update benchmark run test prompt id=%s: %s",
                            result.benchmark_run_test_prompt_id,
                            db_error,
                            exc_info=True,
                        )

                if callback_fn:
                    callback_fn(
                        prompt.state.name.lower(), len(prompts), completed_count, index
                    )
                return result

        # Asynchronously send prompts
        processed_prompts = await asyncio.gather(
            *[
                process_and_count(prompt, index, run_id)
                for index, prompt in enumerate(prompts, start=1)
            ]
        )

        # Process prompts and return the results
        evaluation_summary = await metric_instance.get_results(
            [prompt.evaluation_result for prompt in processed_prompts]
        )

        return processed_prompts, evaluation_summary
