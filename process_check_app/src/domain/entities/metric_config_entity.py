from pydantic import BaseModel

from domain.entities.connector_entity import ConnectorEntity


class MetricConfigEntity(BaseModel):
    """
    MetricConfigEntity represents the configuration for a specific metric.

    Attributes:
        name (str): The name of the metric.
        connector_configurations (dict): A dictionary where the keys are connector types and the values are
        ConnectorEntity instances.
        params (dict): Additional parameters for the metric configuration.
    """

    class Config:
        arbitrary_types_allowed = True

    # The name of the metric
    name: str

    # A dictionary where the keys are connector types and the values are ConnectorEntity instances
    connector_configurations: ConnectorEntity

    # Additional parameters for the metric configuration
    params: dict = {}
