from pydantic import BaseModel


class MoonshotConfigEntity(BaseModel):
    """
    Entity for a single moonshot_config key-value pair.
    """
    id: int | None = None
    key: str
    value: str | None = None
