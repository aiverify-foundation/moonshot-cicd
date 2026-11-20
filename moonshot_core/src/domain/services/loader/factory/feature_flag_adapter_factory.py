import os

from adapters.feature_flag.txt_adapter import TxtAdapter
from domain.ports.feature_flag_port import FeatureFlagPort
from domain.services.app_config import AppConfig


class FeatureFlagAdapterFactory:
    """Select a feature flag adapter by AIVET_FEATURE_FLAGS_SOURCE."""

    _ADAPTERS: dict[str, type[FeatureFlagPort]] = {
        TxtAdapter.SOURCE_NAME: TxtAdapter,
    }

    ERROR_NO_ADAPTER_FOUND = (
        "[FeatureFlagAdapterFactory] No feature flag adapter found for source '{source}'"
    )

    @classmethod
    def get_adapter(cls) -> FeatureFlagPort:
        # Prefer FEATURE_FLAGS_SOURCE_ENV_VAR if set; otherwise default to "file".
        source = os.environ.get(
            AppConfig.FEATURE_FLAGS_SOURCE_ENV_VAR,
            AppConfig.DEFAULT_FEATURE_FLAGS_SOURCE,
        )
        adapter_cls = cls._ADAPTERS.get(source)
        if adapter_cls is None:
            raise RuntimeError(cls.ERROR_NO_ADAPTER_FOUND.format(source=source))
        return adapter_cls()
