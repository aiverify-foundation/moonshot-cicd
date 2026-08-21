from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from domain.entities.custom_app_config_entity import CustomAppConfigEntity


class CustomAppConfigRepository(ABC):
    """Persistence for custom_app_config and parameter rows."""

    @abstractmethod
    def get_by_id(self, config_id: int) -> Optional[CustomAppConfigEntity]:
        pass

    @abstractmethod
    def list_by_app_id(self, custom_app_id: int) -> List[CustomAppConfigEntity]:
        pass

    @abstractmethod
    def get_parameters(self, config_id: int) -> Dict[str, str]:
        pass

    @abstractmethod
    def create(
        self,
        custom_app_id: int,
        name: str,
        parameters: Dict[str, str],
    ) -> CustomAppConfigEntity:
        pass

    @abstractmethod
    def update(
        self,
        config_id: int,
        name: str,
        parameters: Dict[str, str],
    ) -> CustomAppConfigEntity:
        pass
