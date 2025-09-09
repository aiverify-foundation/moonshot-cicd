from typing import Any

from pydantic import BaseModel

from domain.services.enums.task_manager_status import TaskManagerStatus


class PromptEntity(BaseModel):
    """
    PromptEntity represents the structure for storing prompt-related data.

    Attributes:
        index (Any): The position of the prompt in the list.
        prompt (Any): The information used for generating predictions.
        target (Any): The target values or ground truth for comparison.
        model_prediction (Any | None): The result predicted by the model.
        evaluation_result (Any | None): The result of the evaluation process.
        additional_info (dict[str, Any]): Additional information related to the prompt.
        state (TaskManagerStatus): The current state of the prompt.
    """

    class Config:
        arbitrary_types_allowed = True

    # The position of the prompt in the list
    index: Any

    # The information used for generating predictions
    prompt: Any

    # The target values or ground truth for comparison
    target: Any

    # The results predicted by the model
    model_prediction: Any = None

    # The reference context for evaluating the retrieved context
    # This should be in the dataset provided by the user
    reference_context: str = ""

    # The results of the evaluation process
    evaluation_result: Any = None

    # Additional information related to the prompt
    additional_info: dict[str, Any] = {}

    # The current state of the prompt
    state: TaskManagerStatus = TaskManagerStatus.PENDING
