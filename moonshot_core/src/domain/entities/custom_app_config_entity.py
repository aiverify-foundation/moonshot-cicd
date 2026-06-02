from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomAppConfigEntity(BaseModel):
    """Domain entity for a custom_app_config row."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    custom_app_id: int
    name: str
    update_dt: Optional[datetime] = None
