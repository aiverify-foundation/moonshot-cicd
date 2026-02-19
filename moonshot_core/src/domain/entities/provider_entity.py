from typing import Dict
from pydantic import BaseModel, ConfigDict


class ProviderEntity(BaseModel):
    """
    ProviderEntity represents the configuration and metadata for an LLM provider.

    Attributes:
        id (str): Unique identifier for the provider.
        name (str): Display name of the provider.
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

    # Default model to use for this provider
    defaultModel: str = ""

    # Explanation text for the model input field
    modelTextboxExplanation: str = ""

    # Default configuration key-value pairs
    defaultConfigPairs: Dict[str, str] = {}

    # Token or identifier used for model selection
    modelToken: str = ""
