from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.custom_app_entity import CustomAppEntity


class CustomAppRepository(ABC):
    """Persistence for custom_app rows."""

    @abstractmethod
    def get_by_id(self, app_id: int) -> Optional[CustomAppEntity]:
        pass

    @abstractmethod
    def list_all(self) -> List[CustomAppEntity]:
        pass

    @abstractmethod
    def add(self, name: str) -> CustomAppEntity:
        pass
