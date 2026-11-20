import os

from domain.ports.feature_flag_port import FeatureFlagPort
from domain.services.app_config import AppConfig
from domain.services.loader.factory.storage_provider_factory import (
    StorageProviderFactory,
)
from domain.services.logger import configure_logger

logger = configure_logger(__name__)


class TxtAdapter(FeatureFlagPort):
    """
    Adapter for NAME=true/false text files used by feature flags.
    """

    SOURCE_NAME = "file"

    ERROR_FORMAT = "[TxtAdapter] Error formatting feature flags: {error}"
    ERROR_PARSE = "[TxtAdapter] Error parsing feature flags: {error}"
    ERROR_LOAD = "[TxtAdapter] Error loading feature flags from {path}: {error}"
    ERROR_INVALID_LINE = "[TxtAdapter] Skipping invalid line: {line}"

    TRUE_VALUES = frozenset({"true"})
    FALSE_VALUES = frozenset({"false"})

    def load_flags(self) -> dict[str, bool]:
        """
        Load flags from the configured txt file via storage.

        Missing or unreadable files return an empty dict.
        """
        path = self._resolve_path()
        try:
            storage = StorageProviderFactory.get_adapter(path)
            content = storage.read_file(path)
            if content is None:
                return {}
            parsed = self._parse_flags(content)
            if parsed is None:
                return {}
            return parsed
        except Exception as error:
            logger.error(self.ERROR_LOAD.format(path=path, error=error))
            return {}

    def _resolve_path(self) -> str:
        return os.environ.get(
            AppConfig.FEATURE_FLAGS_PATH_ENV_VAR,
            AppConfig.DEFAULT_FEATURE_FLAGS_PATH,
        )

    def format_flags(self, flags: dict[str, bool]) -> str | None:
        """
        Format a mapping of flag names to booleans as NAME=true/false lines.

        Adapter-private helper; not part of FeatureFlagPort.
        """
        try:
            if not isinstance(flags, dict):
                raise TypeError("Cannot format non-dict type to txt flags")
            lines: list[str] = []
            for key in sorted(flags.keys(), key=str):
                value = flags[key]
                if not isinstance(value, bool):
                    raise TypeError("Cannot format non-bool flag value to txt flags")
                lines.append(f"{key}={'true' if value else 'false'}")
            return "\n".join(lines) + ("\n" if lines else "")
        except Exception as e:
            logger.error(self.ERROR_FORMAT.format(error=e))
            return None

    def _parse_flags(self, content: str) -> dict[str, bool] | None:
        """
        Parse NAME=true/false text into a flag mapping.

        Blank lines and # comments are skipped. Invalid lines are logged and skipped.
        """
        try:
            if not isinstance(content, str):
                raise TypeError("Txt content must be a string")
            flags: dict[str, bool] = {}
            for raw_line in content.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    logger.error(self.ERROR_INVALID_LINE.format(line=raw_line))
                    continue
                name, raw_value = line.split("=", 1)
                name = name.strip()
                value = raw_value.strip().lower()
                if not name or value not in self.TRUE_VALUES | self.FALSE_VALUES:
                    logger.error(self.ERROR_INVALID_LINE.format(line=raw_line))
                    continue
                flags[name] = value in self.TRUE_VALUES
            return flags
        except Exception as e:
            logger.error(self.ERROR_PARSE.format(error=e))
            return None
