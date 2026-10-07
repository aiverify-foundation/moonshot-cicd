"""Centralized feature flags for optional product capabilities."""

from __future__ import annotations

from typing import Optional

from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.loader.factory.feature_flag_adapter_factory import (
    FeatureFlagAdapterFactory,
)
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

__all__ = ["FeatureFlagNames", "FeatureFlags"]


class FeatureFlags:
    """
    Loads feature flags via FeatureFlagAdapterFactory (file today; env/DynamoDB later).
    """

    LOG_ERROR_LOADING = "[FeatureFlags] Error loading feature flags: {error}"

    _instance: Optional[FeatureFlags] = None
    _flags: Optional[dict[str, bool]] = None

    def __new__(cls) -> FeatureFlags:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._flags = None
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Clear the cached instance and loaded flags (for tests)."""
        cls._instance = None
        cls._flags = None

    def is_enabled(self, name: str | FeatureFlagNames) -> bool:
        """
        Return whether the named flag is enabled.

        Missing keys and load failures are treated as False.
        """
        return bool(self._load().get(str(name), False))

    def get_all(self) -> dict[str, bool]:
        """
        Return all loaded flags.

        Load failures are treated as an empty mapping (fail-closed).
        """
        return dict(self._load())

    def _load(self) -> dict[str, bool]:
        if FeatureFlags._flags is not None:
            return FeatureFlags._flags
        try:
            adapter = FeatureFlagAdapterFactory.get_adapter()
            data = adapter.load_flags()
            if not isinstance(data, dict):
                FeatureFlags._flags = {}
                return FeatureFlags._flags
            FeatureFlags._flags = {str(key): bool(value) for key, value in data.items()}
            return FeatureFlags._flags
        except Exception as error:
            logger.error(self.LOG_ERROR_LOADING.format(error=error))
            FeatureFlags._flags = {}
            return FeatureFlags._flags
