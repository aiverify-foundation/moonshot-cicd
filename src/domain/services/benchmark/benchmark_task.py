from typing import Callable

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.prompt_entity import PromptEntity
from domain.ports.prompt_processor_port import PromptProcessorPort
from domain.services.enums.task_manager_status import TaskManagerStatus
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class BenchmarkTask:
    """
    Class representing a benchmark task that processes prompts using a specified connector and metric.
    """

    INFO_GENERATING_PROMPTS = "[BenchmarkTask] Generating Prompts..."
    INFO_GENERATING_RESULTS = "[BenchmarkTask] Generating Results..."
    INFO_PROCESSING_PROMPTS = "[BenchmarkTask] Processing Prompts..."
    ERROR_OCCURRED = "[BenchmarkTask] An error occurred: {e}"
    INFO_PROMPTS_COUNT = "[BenchmarkTask] Number of prompts generated: {count}"

    def __init__(
        self,
        task_id: str,
        connector_entity: ConnectorEntity,
        metric: str,
        dataset_entity: DatasetEntity,
        prompt_processor_instance: PromptProcessorPort,
        callback_fn: Callable | None = None,
    ):
        """
        Initialize a BenchmarkTask instance.

        Args:
            task_id (str): The unique identifier for the task.
            connector_entity (ConnectorEntity): The connector entity configuration.
            metric (str): The name of the metric module to be used.
            dataset_entity (DatasetEntity): The dataset entity containing examples to generate prompts from.
            prompt_processor_instance (PromptProcessorPort): The instance of the prompt processor to process prompts.
            callback_fn (Callable | None, optional): An optional callback function to be called after task completion.
        """
        self.task_id = task_id
        self.state = TaskManagerStatus.PENDING
        self.prompts: list[PromptEntity] = []
        self.dataset_entity = dataset_entity
        self.connector_entity = connector_entity
        self.metric = metric
        self.prompt_processor_instance = prompt_processor_instance
        self.callback_fn = callback_fn

    def generate_prompts(self) -> list[PromptEntity]:
        """
        Generate a list of PromptEntity instances from the dataset entity.

        Returns:
            list[PromptEntity]: The list of generated PromptEntity instances.
        """
        logger.info(self.INFO_GENERATING_PROMPTS)

        # Iterate over each example in the dataset entity
        prompts_list = []
        for index, example in enumerate(self.dataset_entity.examples, 1):
            # Extract input and target from the example, defaulting to empty strings if not present
            input: str = example.pop("input", "")
            target: str = example.pop("target", "")

            # Collect any additional key-value pairs from the example
            additional_info = {key: value for key, value in example.items()}

            # Create a new PromptEntity and append it to the prompts list
            prompts_list.append(
                PromptEntity(
                    index=index,
                    prompt=input,
                    target=target,
                    model_prediction=None,
                    evaluation_result={},
                    additional_info=additional_info,
                )
            )

        # Return the list of generated PromptEntity instances
        return prompts_list

    def generate_results(self):
        """
        Generate results for the processed prompts.
        """
        logger.info(self.INFO_GENERATING_RESULTS)

    async def run(self) -> bool:
        """
        Run the benchmark task to process prompts and generate results.

        Returns:
            bool: True if the task completed successfully, False otherwise.
        """
        self.state = TaskManagerStatus.RUNNING
        try:
            self.prompts = self.generate_prompts()
            logger.info(self.INFO_PROMPTS_COUNT.format(count=len(self.prompts)))

            self.prompts_with_results = (
                await self.prompt_processor_instance.process_prompts(
                    self.prompts, self.connector_entity, self.metric, self.callback_fn
                )
            )

            self.generate_results()
            self.state = TaskManagerStatus.COMPLETED
            return True
        except Exception as e:
            logger.error(self.ERROR_OCCURRED.format(e=e))
            self.state = TaskManagerStatus.COMPLETED_WITH_ERRORS
            return False
