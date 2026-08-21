from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderDTO(BaseModel):
    """
    ProviderDTO represents the data transfer object for provider information.

    This DTO contains only the essential data fields for transferring provider
    information between different layers of the application, without complex logic.

    Attributes:
        id (str): Unique identifier for the provider.
        name (str): Display name of the provider.
        system_name (str): Stable system identifier for the provider.
        version (int): Version number of the provider row.
        defaultModel (str): Default model to use for this provider.
        modelTextboxExplanation (str): Explanation text for the model input field.
        defaultConfigPairs (Dict[str, str]): Default configuration key-value pairs.
        modelToken (str): Token or identifier used for model selection.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Unique identifier for the provider
    id: str

    # Display name of the provider
    name: str

    # Stable system identifier for the provider (e.g. "openai", "together_ai")
    system_name: str

    # Version number of the provider row
    version: int

    # Default model to use for this provider
    defaultModel: str = ""

    # Explanation text for the model input field
    modelTextboxExplanation: str = ""

    # Default configuration key-value pairs
    defaultConfigPairs: Dict[str, str] = {}

    # Token or identifier used for model selection
    modelToken: str = ""


class TestLlmProviderConnectionBody(BaseModel):
    """Draft form values used to probe an LLM provider before save."""

    llm_provider_id: int
    model_name: str
    savedConfigPairs: Dict[str, str] = Field(default_factory=dict)
    api_key: Optional[str] = None


class TestLlmProviderConnectionResponseDTO(BaseModel):
    success: bool
    error: Optional[str] = None
    response_preview: Optional[str] = None
