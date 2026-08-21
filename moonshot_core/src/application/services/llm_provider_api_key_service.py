"""Create/update LLM provider API keys in the DB (AES-256-GCM encrypted at rest)."""

from __future__ import annotations

from domain.services.logger import get_logger

from adapters.driven.repository.sqlalchemy.llm_provider_api_key_adapter import (
    LLMProviderApiKeyAdapter,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import LLMProviderModel
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import MoonshotConfigAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.llm_provider_api_key_repository import LlmProviderApiKeyRepository
from application.services.secrets_master_key_service import SecretsMasterKeyService
from domain.services.secret_encryption import (
    EncryptedApiKeyFields,
    LegacyApiKeyStorageError,
    encrypt_api_key,
)

# Alias for callers expecting the ticket / API name.
LlmProviderApiKeyLegacyStorageError = LegacyApiKeyStorageError


class LlmProviderApiKeyUnknownProviderError(Exception):
    """No llm_provider row for the given id."""


class LlmProviderApiKeyService:
    def __init__(
        self,
        repository: LlmProviderApiKeyRepository | None = None,
        session_manager: SessionManager | None = None,
        secrets_master_key: SecretsMasterKeyService | None = None,
    ) -> None:
        self._repository = repository or LLMProviderApiKeyAdapter()
        self._session_manager = session_manager or SessionManager.get_instance()
        self._secrets_master_key = secrets_master_key or SecretsMasterKeyService(
            MoonshotConfigAdapter()
        )
        self._logger = get_logger(__name__)

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

    def _encrypt(self, api_key: str) -> EncryptedApiKeyFields:
        master = self._secrets_master_key.get_or_create_master_key_bytes()
        return encrypt_api_key(api_key, master)

    def create_api_key(self, llm_provider_id: int, api_key: str) -> None:
        if not api_key:
            raise ValueError("api_key must be non-empty")
        self._ensure_provider_exists(llm_provider_id)
        self._logger.info("Creating API key row for llm_provider_id=%s", llm_provider_id)
        self._repository.insert(llm_provider_id, self._encrypt(api_key))

    def set_api_key(self, llm_provider_id: int, api_key: str) -> None:
        """Store an API key for the provider, replacing any existing row(s)."""
        if not api_key:
            raise ValueError("api_key must be non-empty")
        self._ensure_provider_exists(llm_provider_id)
        self._logger.info("Setting API key for llm_provider_id=%s", llm_provider_id)
        self._repository.replace(llm_provider_id, self._encrypt(api_key))

    def update_api_key(self, llm_provider_id: int, api_key: str) -> None:
        if not api_key:
            raise ValueError("api_key must be non-empty")
        self._ensure_provider_exists(llm_provider_id)
        self._logger.info("Updating API key row for llm_provider_id=%s", llm_provider_id)
        self._repository.update(llm_provider_id, self._encrypt(api_key))
