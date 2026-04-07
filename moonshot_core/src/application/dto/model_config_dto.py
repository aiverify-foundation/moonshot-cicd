from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from application.dto.provider_dto import ProviderDTO


class ModelConfigDTO(BaseModel):
    """
    ModelConfigDTO represents the data transfer object for model configuration information.
    
    This DTO contains only the essential data fields for transferring model configuration
    information between different layers of the application, without complex logic.

    Attributes:
        id (str): Unique identifier for the model configuration.
        name (str): Display name of the model configuration.
        modelname (str): Name of the model this configuration is for.
        providerID (str): ID of the provider that owns this model.
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

    # ID of the provider that owns this model
    providerID: str

    # Saved configuration key-value pairs
    savedConfigPairs: Dict[str, str] = {}

    # Timestamp when this configuration was last updated
    lastUpdated: datetime


class LLMProviderModelInfoDTO(BaseModel):
    """
    Lightweight DTO representing a row in the llm_provider_model table for a provider.
    """

    id: int
    name: str
    create_dt: datetime


class LLMProviderEndpointConfigInfoDTO(BaseModel):
    """
    Lightweight DTO representing a row in the llm_provider_endpoint_config table for a provider.
    """

    id: int
    name: str


class LLMProviderDetailsDTO(BaseModel):
    """
    Aggregated DTO containing an LLM provider and its related models and endpoint configs.
    """

    provider: ProviderDTO
    models: List[LLMProviderModelInfoDTO]
    endpoint_configs: List[LLMProviderEndpointConfigInfoDTO]
    config_params: Optional[Dict[str, str]] = None


class ProviderDatabaseConfigsDTO(BaseModel):
    """
    One llm_provider row's display name plus model configs read from the database only
    (llm_provider_model_config + llm_provider_endpoint_config_parameters), not file/SQLite stores.
    """

    providerName: str
    configs: List[ModelConfigDTO]
