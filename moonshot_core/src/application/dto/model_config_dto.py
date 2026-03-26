from typing import Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ModelConfigDTO(BaseModel):
    """
    ModelConfigDTO represents the data transfer object for model configuration information.
    
    This DTO contains only the essential data fields for transferring model configuration
    information between different layers of the application, without complex logic.

    Attributes:
        id (str): Unique identifier for the model configuration.
        name (str): Display name of the model configuration.
        modelname (str): Name of the model this configuration is for.
        providerID (str): Provider system_name (preferred) or legacy display name.
        provider_version (int): Matches llm_provider.version when resolving provider.
        savedConfigPairs (Dict[str, str]): Saved configuration key-value pairs.
        lastUpdated (datetime): Timestamp when this configuration was last updated.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Unique identifier for the model configuration
    id: str

    # Display name of the model configuration
    name: str

    # Name of the model this configuration is for
    modelname: str

    # Provider system_name (preferred) or legacy display name
    providerID: str

    # Matches llm_provider.version when resolving providerID
    provider_version: int = 0

    # Saved configuration key-value pairs
    savedConfigPairs: Dict[str, str] = {}

    # Timestamp when this configuration was last updated
    lastUpdated: datetime
