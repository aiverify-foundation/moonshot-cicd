import asyncio
from typing import Callable

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.prompt_entity import PromptEntity
from domain.entities.benchmark_run_test_error_entity import (
    BenchmarkRunTestErrorEntity,
)
from domain.ports.connector_port import ConnectorPort
from domain.ports.metric_port import MetricPort
from domain.ports.prompt_processor_port import PromptProcessorPort
from domain.services.app_config import AppConfig
from domain.services.enums.module_types import ModuleTypes
from domain.services.enums.task_manager_status import TaskManagerStatus
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger
from domain.services.prompt_error_evaluation import (
    FAILED_EVALUATED_RESULT,
    entities_for_aggregation,
    synthetic_error_entity,
)

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
    ) -> PromptEntity:
        """
        Asynchronously process a single prompt entity using the provided connector and metric instances.

        Args:
            prompt_entity (PromptEntity): The prompt entity to be processed.
            connector_instance (ConnectorPort): The connector instance to process the prompt.
            metric_instance (MetricPort): The metric instance to evaluate the processed prompt.

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

            try:
                evaluated_result = await metric_instance.get_individual_result(
                    metric_entity
                )
            except Exception as e:
                prompt_entity.state = TaskManagerStatus.ERROR
                prompt_entity.additional_info["error_source"] = "metric"
                logger.error(f"{self.ERROR_PROCESSING_PROMPT} {e}")
                raise

            metric_entity.evaluated_result = evaluated_result
            prompt_entity.evaluation_result = metric_entity

            # Set the prompt entity state to completed
            prompt_entity.state = TaskManagerStatus.COMPLETED
        except Exception as e:
            if prompt_entity.state != TaskManagerStatus.ERROR:
                prompt_entity.state = TaskManagerStatus.ERROR
                prompt_entity.additional_info["error_source"] = "connector"
            logger.error(f"{self.ERROR_PROCESSING_PROMPT} {e}")
            raise

        return prompt_entity

    async def process_prompts(
        self,
        prompts: list[PromptEntity],
        connector_entity: ConnectorEntity,
        metric: dict,
        callback_fn: Callable | None = None,
        write_to_db: bool = False,
        run_test_id: int | None = None,
    ) -> tuple[list[PromptEntity], dict]:
        """
        Asynchronously process a list of prompt entities concurrently using the specified connector and metric modules.

        Args:
            prompts (list[PromptEntity]): The list of prompt entities to be processed.
            connector_entity (ConnectorEntity): The connector entity configuration.
            metric (str): The name of the metric module to be loaded.
            callback_fn (Callable | None): The callback function to update the progress.
            write_to_db (bool): Whether to write results to the database.
            run_test_id (int | None): Optional. When provided and write_to_db is True, used when updating
                benchmark_run_test_prompt rows (e.g. from benchmark run execution service).

        Returns:
            tuple[list[PromptEntity], dict]: A tuple containing the list of processed prompt entities with model
            predictions and evaluation results, and the evaluation summary.
        """
        # Use asyncio.gather to process all prompts concurrently
        # Load existing run_test_prompts by run_test_id when write_to_db (for id-based update only)
        existing_run_test_prompts: list = []
        prompt_repo = None
        error_repo = None
        if write_to_db and run_test_id is not None:
            try:
                from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import (
                    SqlAlchemyBenchmarkRunTestPromptRepository,
                )
                from adapters.driven.repository.sqlalchemy.benchmark_run_test_error_adapter import (
                    SqlAlchemyBenchmarkRunTestErrorRepository,
                )
                prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
                error_repo = SqlAlchemyBenchmarkRunTestErrorRepository()
                existing_run_test_prompts = prompt_repo.get_all_by_run_test_id(run_test_id)
            except Exception as db_error:
                logger.error(
                    "[AsyncioPromptProcessor] Failed to load run test prompts for run_test_id=%s: %s",
                    run_test_id,
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
            if metric_config is None:
                raise ValueError(
                    f"No metric configuration found for {met_id!r} in app config "
                    "(check moonshot_config.yaml metrics section)."
                )
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
            prompt: PromptEntity, index: int, run_test_id: int | None = None
        ) -> PromptEntity:
            """
            Asynchronously process a single prompt entity and update the completion count.

            Args:
                prompt (PromptEntity): The prompt entity to be processed.
                index (int): The index of the prompt in the list.
                run_test_id (int | None): Optional benchmark_run_test_status id for DB updates when write_to_db.

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

                error_message: str | None = None
                error_source: str | None = None
                try:
                    result = await self.process_single_prompt(
                        prompt,
                        connector_instance,
                        metric_instance,
                    )
                except Exception as e:
                    error_message = str(e)
                    error_source = prompt.additional_info.get("error_source", "unknown")
                    result = prompt
                    result.evaluation_result = synthetic_error_entity(prompt)

                completed_count += 1

                # Update existing benchmark_run_test_prompt row by id when set (no insert)
                if (
                    write_to_db
                    and run_test_id is not None
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
                            entity.status = result.state.name.lower()
                            if error_message is None:
                                if hasattr(result.model_prediction, "response"):
                                    entity.prediction_result = (
                                        result.model_prediction.response
                                    )
                                else:
                                    entity.prediction_result = (
                                        str(result.model_prediction)
                                        if result.model_prediction is not None
                                        else None
                                    )
                                metric_entity = result.evaluation_result
                                evaluated = (
                                    metric_entity.evaluated_result
                                    if metric_entity
                                    else None
                                )
                                entity.evaluation_prediction_result = (
                                    str(evaluated) if evaluated is not None else None
                                )
                                entity.evaluation_accuracy = (
                                    float(evaluated)
                                    if isinstance(evaluated, (int, float))
                                    else None
                                )
                            else:
                                entity.evaluation_prediction_result = str(
                                    FAILED_EVALUATED_RESULT
                                )
                                entity.evaluation_accuracy = 0.0
                            prompt_repo.update(entity)
                            if error_message is not None and error_repo is not None:
                                error_repo.save(
                                    BenchmarkRunTestErrorEntity(
                                        benchmark_run_test_prompt_id=result.benchmark_run_test_prompt_id,
                                        error_message=error_message,
                                        error_source=error_source or "unknown",
                                    )
                                )
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
                process_and_count(prompt, index, run_test_id)
                for index, prompt in enumerate(prompts, start=1)
            ]
        )

        aggregation_entities = entities_for_aggregation(processed_prompts)
        evaluation_summary = await metric_instance.get_results(aggregation_entities)

        return processed_prompts, evaluation_summary
