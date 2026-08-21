from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomAppEntity(BaseModel):
    """Domain entity for a custom_app row."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    name: str
