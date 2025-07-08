from abc import ABC, abstractmethod
from typing import Callable

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.prompt_entity import PromptEntity


class PromptProcessorPort(ABC):
    """
    Abstract base class for prompt processing operations.

    This class defines the interface for processing prompts using a specified connector and metric.
    Implementations of this class should provide concrete methods for these operations.
    """

    @abstractmethod
    async def process_prompts(
        self,
        prompts: list[PromptEntity],
        connector_entity: ConnectorEntity,
        metric: str,
        callback_fn: Callable | None = None,
    ) -> list[PromptEntity]:
        """
        Asynchronously process a list of prompts using the provided connector and metric.

        Args:
            prompts (list[PromptEntity]): A list of PromptEntity instances to be processed.
            connector_entity (ConnectorEntity): The connector entity containing connector-specific data.
            metric (str): The name of the metric to be used for evaluating the prompts.
            callback_fn (Callable | None): A callback function to be executed after the prompts are processed.

        Returns:
            list[PromptEntity]: A list of processed PromptEntity instances with updated results.
        """
        pass
