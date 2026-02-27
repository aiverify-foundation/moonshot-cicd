"""File-based implementation of SharedConfigRepository for shared.yaml-style config."""

import yaml
from pathlib import Path

from application.ports.shared_config_repository import SharedConfigRepository
from domain.services.logger import configure_logger


class FileSharedConfigRepository(SharedConfigRepository):
    """
    Reads shared test config from a YAML file and provides last-modified time.
    """

    def __init__(self) -> None:
        self.logger = configure_logger(__name__)

    def get_config(self, path: Path) -> dict:
        """Load and parse YAML from path. Raises on missing file or invalid structure."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected top-level dict in {path}, got {type(data).__name__}"
            )
        return data

    def get_last_modified(self, path: Path) -> float:
        """Return file last modified time as float."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        return path.stat().st_mtime
