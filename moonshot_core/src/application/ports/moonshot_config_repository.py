from abc import ABC, abstractmethod
from typing import Dict, Optional

from domain.entities.moonshot_config_entity import MoonshotConfigEntity


class MoonshotConfigRepository(ABC):
    """Abstract repository for application config key-value storage (moonshot_config table)."""

    @abstractmethod
    def get_by_key(self, key: str) -> Optional[MoonshotConfigEntity]:
        """Get a config entry by key. Returns None if not found."""
        pass

    @abstractmethod
    def set(self, key: str, value: str | None) -> MoonshotConfigEntity:
        """Set (upsert) a config entry by key. Returns the saved entity."""
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, str | None]:
        """Return all config entries as a dict key -> value."""
        pass

    @abstractmethod
    def delete_by_key(self, key: str) -> bool:
        """Delete config entry by key. Returns True if deleted, False if not found."""
        pass
