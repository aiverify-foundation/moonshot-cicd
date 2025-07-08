from typing import Any

from pydantic import BaseModel

from domain.entities.connector_response_entity import ConnectorResponseEntity


class MetricIndividualEntity(BaseModel):
    """
    MetricIndividualEntity represents the structure for storing individual metric-related data.

    Attributes:
        prompt (Any): The prompt used for generating predictions.
        predicted_result (ConnectorResponseEntity): The result predicted by the connector.
        target (Any): The target values or ground truth for comparison.
        evaluated_result (Any | None): The result of the evaluation process, defaults to None.
    """

    class Config:
        arbitrary_types_allowed = True

    # The prompt used for generating predictions
    prompt: Any

    # The result predicted by the model
    predicted_result: ConnectorResponseEntity

    # The target values or ground truth for comparison
    target: Any

    # The reference context for evaluating the retrieved context
    reference_context: str = ""

    # The result of the evaluation process
    evaluated_result: Any = None
