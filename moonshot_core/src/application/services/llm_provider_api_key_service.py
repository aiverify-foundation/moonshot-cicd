"""Create/update LLM provider API keys in the relational DB (stored raw for now)."""

from __future__ import annotations

from adapters.driven.repository.sqlalchemy.llm_provider_api_key_adapter import (
    LLMProviderApiKeyAdapter,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import LLMProviderModel
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.llm_provider_api_key_repository import LlmProviderApiKeyRepository
from domain.services.logger import configure_logger


class LlmProviderApiKeyUnknownProviderError(Exception):
    """No llm_provider row for the given id."""


class LlmProviderApiKeyService:
    def __init__(
        self,
        repository: LlmProviderApiKeyRepository | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        self._repository = repository or LLMProviderApiKeyAdapter()
        self._session_manager = session_manager or SessionManager.get_instance()
        self._logger = configure_logger(__name__)

    def _ensure_provider_exists(self, llm_provider_id: int) -> None:
        with self._session_manager.get_session() as session:
            prov = (
                session.query(LLMProviderModel)
                .filter(LLMProviderModel.id == llm_provider_id)
                .first()
            )
            if prov is None:
                raise LlmProviderApiKeyUnknownProviderError(
                    f"No llm_provider with id={llm_provider_id}"
                )

    def create_api_key(self, llm_provider_id: int, api_key: str) -> None:
        if not api_key:
            raise ValueError("api_key must be non-empty")
        self._ensure_provider_exists(llm_provider_id)
        self._logger.info("Creating API key row for llm_provider_id=%s", llm_provider_id)
        self._repository.insert(llm_provider_id, api_key)

    def update_api_key(self, llm_provider_id: int, api_key: str) -> None:
        if not api_key:
            raise ValueError("api_key must be non-empty")
        self._ensure_provider_exists(llm_provider_id)
        self._logger.info("Updating API key row for llm_provider_id=%s", llm_provider_id)
        self._repository.update(llm_provider_id, api_key)
