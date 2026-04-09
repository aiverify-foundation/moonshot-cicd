from abc import ABC, abstractmethod


class LlmProviderApiKeyConflictError(Exception):
    """An API key row already exists for this llm_provider_id."""


class LlmProviderApiKeyNotFoundError(Exception):
    """No API key row exists for this llm_provider_id."""


class LlmProviderApiKeyAmbiguousError(Exception):
    """More than one API key row exists for this llm_provider_id."""


class LlmProviderApiKeyRepository(ABC):
    """Persistence for llm_provider_api_key rows (insert vs update, no upsert)."""

    @abstractmethod
    def insert(self, llm_provider_id: int, api_key: str) -> None:
        """
        Insert a new API key row. Raises LlmProviderApiKeyConflictError if any row
        already exists for llm_provider_id.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, llm_provider_id: int, api_key: str) -> None:
        """
        Update the single API key row for llm_provider_id.
        Raises LlmProviderApiKeyNotFoundError if none, LlmProviderApiKeyAmbiguousError if many.
        """
        raise NotImplementedError
