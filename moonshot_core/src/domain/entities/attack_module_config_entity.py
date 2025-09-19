from pydantic import BaseModel

from domain.entities.connector_entity import ConnectorEntity


class AttackModuleConfigEntity(BaseModel):
    """
    AttackModuleConfigEntity represents the configuration for a specific attack module.

    Attributes:
        name (str): The name of the attack module.
        connector_configurations (dict): A dictionary of connector configurations associated with the attack module.
        params (dict): Additional parameters for the attack module configuration.
    """

    class Config:
        arbitrary_types_allowed = True

    # The name of the attack module
    name: str

    # A dictionary of connector configurations associated with the attack module
    connector_configurations: dict[str, ConnectorEntity]

    # Additional parameters for the attack module configuration
    params: dict = {}
