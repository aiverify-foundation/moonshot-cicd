from typing import Dict
from pydantic import BaseModel


class ProviderDTO(BaseModel):
    """
    ProviderDTO represents the data transfer object for provider information.
    
    This DTO contains only the essential data fields for transferring provider
    information between different layers of the application, without complex logic.

    Attributes:
        id (str): Unique identifier for the provider.
        name (str): Display name of the provider.
        defaultModel (str): Default model to use for this provider.
        modelTextboxExplanation (str): Explanation text for the model input field.
        defaultConfigPairs (Dict[str, str]): Default configuration key-value pairs.
        modelToken (str): Token or identifier used for model selection.
    """

    class Config:
        arbitrary_types_allowed = True

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
