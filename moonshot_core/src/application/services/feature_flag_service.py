"""Application service for reading feature flags."""

from __future__ import annotations

from application.dto.feature_flags_dto import FeatureFlagsResponseDTO
from domain.services.feature_flags import FeatureFlags


class FeatureFlagService:
    """Expose loaded feature flags to API entrypoints."""

    def get_flags(self) -> FeatureFlagsResponseDTO:
        return FeatureFlagsResponseDTO(flags=FeatureFlags().get_all())
