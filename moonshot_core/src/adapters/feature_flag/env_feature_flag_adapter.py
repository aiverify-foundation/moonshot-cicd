import os

from domain.ports.feature_flag_port import FeatureFlagPort
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.logger import configure_logger

logger = configure_logger(__name__)


class EnvFeatureFlagAdapter(FeatureFlagPort):
    """
    Loads feature-flag overrides from process environment variables.

    Only known flag names (FeatureFlagNames) are read. Invalid values are logged
    and omitted from the result.
    """

    SOURCE_NAME = "env"

    LOG_INVALID_ENV_VALUE = (
        "[EnvFeatureFlagAdapter] Skipping invalid env value for {name}={value!r}"
    )

    _TRUE_VALUES = frozenset({"true"})
    _FALSE_VALUES = frozenset({"false"})

    def load_flags(self) -> dict[str, bool]:
        flags: dict[str, bool] = {}
        for name in FeatureFlagNames:
            key = str(name)
            if key not in os.environ:
                continue
            parsed = self._parse_bool(os.environ[key])
            if parsed is None:
                logger.error(
                    self.LOG_INVALID_ENV_VALUE.format(name=key, value=os.environ[key])
                )
                continue
            flags[key] = parsed
        return flags

    def _parse_bool(self, raw_value: str) -> bool | None:
        value = raw_value.strip().lower()
        if value in self._TRUE_VALUES:
            return True
        if value in self._FALSE_VALUES:
            return False
        return None
