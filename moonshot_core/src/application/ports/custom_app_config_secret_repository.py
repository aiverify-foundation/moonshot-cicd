from abc import ABC, abstractmethod
from typing import List

from domain.services.secret_encryption import EncryptedApiKeyFields


class CustomAppConfigSecretConflictError(Exception):
    """A secret row already exists for this config_id and key."""


class CustomAppConfigSecretNotFoundError(Exception):
    """No secret row exists for this config_id and key."""


class CustomAppConfigSecretRepository(ABC):
    """Persistence for custom_app_config_secrets rows."""

    @abstractmethod
    def insert(self, config_id: int, key: str, payload: EncryptedApiKeyFields) -> None:
        pass

    @abstractmethod
    def update(self, config_id: int, key: str, payload: EncryptedApiKeyFields) -> None:
        pass

    @abstractmethod
    def replace(self, config_id: int, key: str, payload: EncryptedApiKeyFields) -> None:
        pass

    @abstractmethod
    def get_encrypted(self, config_id: int, key: str) -> EncryptedApiKeyFields:
        pass

    @abstractmethod
    def list_keys(self, config_id: int) -> List[str]:
        pass
