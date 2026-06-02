from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateCustomAppBody(BaseModel):
    name: str


class CustomAppResponseDTO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    name: str


class CreateCustomAppConfigBody(BaseModel):
    name: str
    savedConfigPairs: Dict[str, str] = Field(default_factory=dict)


class UpdateCustomAppConfigBody(BaseModel):
    name: str
    savedConfigPairs: Dict[str, str] = Field(default_factory=dict)


class CustomAppConfigResponseDTO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    custom_app_id: int
    name: str
    savedConfigPairs: Dict[str, str] = Field(default_factory=dict)
    update_dt: Optional[datetime] = None
    api_key_configured: bool = Field(
        default=False,
        description=(
            "True if a custom_app_config_secrets row exists for key api_key "
            "(no secret exposed)."
        ),
    )


class SetCustomAppConfigSecretBody(BaseModel):
    secret: str
