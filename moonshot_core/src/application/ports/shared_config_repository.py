"""Abstract repository for reading shared test config (e.g. shared.yaml)."""

from abc import ABC, abstractmethod
from pathlib import Path


class SharedConfigRepository(ABC):
    """Abstract repository for shared test config file access."""

    @abstractmethod
    def get_config(self, path: Path) -> dict:
        """
        Load and parse the config file at path (e.g. YAML) and return as dict.

        Args:
            path: Path to the config file (e.g. shared.yaml).

        Returns:
            Parsed config as a dict (top-level bundle keys, each with tests, etc.).

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file content is not valid (e.g. not a dict).
        """
        pass

    @abstractmethod
    def get_last_modified(self, path: Path) -> float:
        """
        Return the last modified time of the file at path (e.g. for change detection).

        Args:
            path: Path to the file.

        Returns:
            Last modified time as a float (e.g. from stat().st_mtime).

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        pass
