from abc import ABC, abstractmethod

from domain.services.secret_encryption import EncryptedApiKeyFields


class LlmProviderApiKeyConflictError(Exception):
    """An API key row already exists for this llm_provider_id."""


class LlmProviderApiKeyNotFoundError(Exception):
    """No API key row exists for this llm_provider_id."""


class LlmProviderApiKeyAmbiguousError(Exception):
    """More than one API key row exists for this llm_provider_id."""


class LlmProviderApiKeyRepository(ABC):
    """Persistence for llm_provider_api_key rows (insert, update, replace)."""

    @abstractmethod
    def insert(self, llm_provider_id: int, payload: EncryptedApiKeyFields) -> None:
        """
        Insert a new encrypted API key row. Raises LlmProviderApiKeyConflictError if any row
        already exists for llm_provider_id.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, llm_provider_id: int, payload: EncryptedApiKeyFields) -> None:
        """
        Update the single API key row for llm_provider_id.
        Raises LlmProviderApiKeyNotFoundError if none, LlmProviderApiKeyAmbiguousError if many.
        """
        raise NotImplementedError

    @abstractmethod
    def replace(self, llm_provider_id: int, payload: EncryptedApiKeyFields) -> None:
        """
        Remove any existing API key rows for llm_provider_id and insert one new row.
        """
        raise NotImplementedError
