from typing import Dict
from datetime import datetime
from pydantic import BaseModel


class ModelConfigEntity(BaseModel):
    """
    ModelConfigEntity represents the configuration and metadata for a model configuration.

    Attributes:
        id (str): Unique identifier for the model configuration.
        name (str): Display name of the model configuration.
        modelname (str): Name of the model this configuration is for.
        providerID (str): ID of the provider that owns this model.
        savedConfigPairs (Dict[str, str]): Saved configuration key-value pairs.
        lastUpdated (datetime): Timestamp when this configuration was last updated.
    """

    class Config:
        arbitrary_types_allowed = True

    # Unique identifier for the model configuration
    id: str

    # Display name of the model configuration
    name: str

    # Name of the model this configuration is for
    modelname: str

    # ID of the provider that owns this model
    providerID: str

    # Saved configuration key-value pairs
    savedConfigPairs: Dict[str, str] = {}

    # Timestamp when this configuration was last updated
    lastUpdated: datetime
