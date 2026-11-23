"""DTOs for feature flag read APIs."""

from pydantic import BaseModel, Field


class FeatureFlagsResponseDTO(BaseModel):
    """Live feature flag name → enabled mapping."""

    flags: dict[str, bool] = Field(
        default_factory=dict,
        description="Feature flag names mapped to enabled state",
    )
