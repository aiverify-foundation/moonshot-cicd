from typing import Callable, Optional

from pydantic import BaseModel


class AttackModuleEntity(BaseModel):
    """
    AttackModuleEntity represents the structure for storing attack module-related data.

    Attributes:
        connector (str): The connector to use.
        metric (dict): The metric to be used.
        prompt (str): The user's prompt.
        dataset (str): The user's dataset.
        prompt_processor (str): The prompt processor to use. Defaults to asyncio_prompt_processor_adapter.
        callback_fn (Optional[Callable]): The callback function to be executed after the attack module runs.
    """

    class Config:
        arbitrary_types_allowed = True

    # The connector to use
    connector: str

    # The metric to be used
    metric: dict

    # The user's prompt
    prompt: str = ""

    # The user's dataset
    dataset: str = ""

    # The prompt processor to use. Defaults to asyncio_prompt_processor_adapter
    prompt_processor: str

    # The callback function to be executed after the attack module runs
    callback_fn: Optional[Callable] = None
