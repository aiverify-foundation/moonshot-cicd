import asyncio
from typing import Callable

from domain.entities.connector_entity import ConnectorEntity
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

            evaluated_result = await metric_instance.get_individual_result(
                metric_entity
            )

            metric_entity.evaluated_result = evaluated_result
            prompt_entity.evaluation_result = metric_entity

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
    ) -> tuple[list[PromptEntity], dict]:
        """
        Asynchronously process a list of prompt entities concurrently using the specified connector and metric modules.

        Args:
            prompts (list[PromptEntity]): The list of prompt entities to be processed.
            connector_entity (ConnectorEntity): The connector entity configuration.
            metric (str): The name of the metric module to be loaded.
            callback_fn (Callable | None): The callback function to update the progress.

        Returns:
            tuple[list[PromptEntity], dict]: A tuple containing the list of processed prompt entities with model
            predictions and evaluation results, and the evaluation summary.
        """
        # Use asyncio.gather to process all prompts concurrently
        try:
            # Load and configure the connector instance
            connector_instance, _ = ModuleLoader.load(
                connector_entity.connector_adapter, ModuleTypes.CONNECTOR
            )
            connector_instance.configure(connector_entity)
            logger.info(self.CONNECTOR_LOADED_MSG)
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
            logger.info(self.METRIC_LOADED_MSG)
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

        async def process_and_count(prompt: PromptEntity, index: int) -> PromptEntity:
            """
            Asynchronously process a single prompt entity and update the completion count.

            Args:
                prompt (PromptEntity): The prompt entity to be processed.
                index (int): The index of the prompt in the list.

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
                    prompt, connector_instance, metric_instance
                )
                completed_count += 1

                if callback_fn:
                    callback_fn(
                        prompt.state.name.lower(), len(prompts), completed_count, index
                    )
                return result

        # Asynchronously send prompts
        processed_prompts = await asyncio.gather(
            *[
                process_and_count(prompt, index)
                for index, prompt in enumerate(prompts, start=1)
            ]
        )

        # Process prompts and return the results
        evaluation_summary = await metric_instance.get_results(
            [prompt.evaluation_result for prompt in processed_prompts]
        )

        return processed_prompts, evaluation_summary
