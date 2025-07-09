from pydantic import BaseModel


class ConnectorEntity(BaseModel):
    """
    ConnectorEntity represents the configuration and parameters for a model connector.

    Attributes:
        connector_adapter (str): The connector adapter name.
        model (str): The model name or identifier.
        model_endpoint (str): The endpoint URL for the model.
        params (dict): Parameters for the model.
        connector_pre_prompt (str): Pre-prompt text for the connector.
        connector_post_prompt (str): Post-prompt text for the connector.
        system_prompt (str): System prompt text.
    """

    class Config:
        arbitrary_types_allowed = True

    # The connector adapter name
    connector_adapter: str

    # The model name or identifier
    model: str

    # The endpoint URL for the model
    model_endpoint: str = ""

    # Parameters for the model
    params: dict = {}

    # Pre-prompt text for the connector
    connector_pre_prompt: str = ""

    # Post-prompt text for the connector
    connector_post_prompt: str = ""

    # System prompt text
    system_prompt: str = ""
