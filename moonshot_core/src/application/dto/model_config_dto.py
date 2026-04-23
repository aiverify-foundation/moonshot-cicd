from typing import Dict, List, Optional, Self
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator

from application.dto.provider_dto import ProviderDTO


class CreateDatabaseModelConfigBody(BaseModel):
    """Payload for POST /api/database-model-configs (relational store only)."""

    model_config = ConfigDict(extra="forbid")

    model_id: Optional[int] = None
    llm_provider_id: Optional[int] = None
    model_name: Optional[str] = None
    name: str
    savedConfigPairs: Dict[str, str] = Field(default_factory=dict)
    last_used_dt: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_model_reference(self) -> Self:
        by_id = self.model_id is not None
        if by_id:
            if self.llm_provider_id is not None or (
                self.model_name is not None and self.model_name.strip() != ""
            ):
                raise ValueError(
                    "When model_id is set, omit llm_provider_id and model_name"
                )
            return self
        if self.llm_provider_id is None:
            raise ValueError(
                "Provide model_id or both llm_provider_id and a non-empty model_name"
            )
        if not self.model_name or not self.model_name.strip():
            raise ValueError("model_name must be non-empty when creating by provider")
        return self


class UpdateDatabaseModelConfigBody(BaseModel):
    """Payload for PUT /api/database-model-configs/{config_id} (relational store only)."""

    model_config = ConfigDict(extra="forbid")

    model_id: int
    name: str
    savedConfigPairs: Dict[str, str] = Field(default_factory=dict)
    last_used_dt: Optional[datetime] = None


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

    # llm_provider_model.id this configuration belongs to (for portal FK wiring)
    modelId: int = 0

    # ID of the provider that owns this model
    providerID: str

    # Matches llm_provider.version when resolving providerID (file/SQLite configs)
    provider_version: int = 0

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
    database_model_configs: List[ModelConfigDTO] = Field(
        default_factory=list,
        description="Relational model configs (llm_provider_model_config + parameters) for benchmark FKs.",
    )
    api_key_configured: bool = Field(
        default=False,
        description="True if at least one llm_provider_api_key row exists for this provider (no secret exposed).",
    )


class ProviderDatabaseConfigsDTO(BaseModel):
    """
    One llm_provider row's display name plus model configs read from the database only
    (llm_provider_model_config + llm_provider_model_config_parameters), not file/SQLite stores.
    """

    providerName: str
    configs: List[ModelConfigDTO]
