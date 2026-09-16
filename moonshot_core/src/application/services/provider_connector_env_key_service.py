"""Ensure connector adapters see an API key: prefer DB provider key, else environment."""

from __future__ import annotations

import os

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderApiKeyModel,
    LLMProviderModel,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import MoonshotConfigAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.secrets_master_key_service import SecretsMasterKeyService
from domain.services.feature_flags import (
    OPENROUTER_ADAPTER_SYSTEM_NAME,
    is_openrouter_enabled,
)
from domain.services.logger import configure_logger
from domain.services.secret_encryption import (
    LegacyApiKeyStorageError,
    SecretDecryptionError,
    decrypt_api_key,
)

logger = configure_logger(__name__)


def get_adapter_module_to_env() -> dict[str, str]:
    """Connector module name -> env var the adapter reads (OpenRouter gated by feature flag)."""
    mapping = {
        "openai_adapter": "OPENAI_API_KEY",
        "together_adapter": "TOGETHER_API_KEY",
    }
    if is_openrouter_enabled():
        mapping[OPENROUTER_ADAPTER_SYSTEM_NAME] = "OPENROUTER_API_KEY"
    return mapping


# Backward-compatible name; prefer get_adapter_module_to_env() for flag-aware lookups.
ADAPTER_MODULE_TO_ENV: dict[str, str] = get_adapter_module_to_env()


class ProviderConnectorEnvKeyService:
    """
    When running benchmarks against a DB-resolved connector, adapters that only read ``os.environ``
    need the API key injected. ``OpenAIAdapter``, ``TogetherAdapter``, and ``OpenRouterAdapter``
    (when enabled) resolve keys via ``llm_provider.system_name`` (see
    ``ConnectorPort.require_system_name_and_version``); other adapters rely on env populated by
    ``ensure_provider_api_key_in_environment``.

    Prefer a decrypted key from ``llm_provider_api_key`` before any non-empty environment value.
    """

    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()

    def get_plain_api_key_for_provider_system_name(
        self, *, provider_system_name: str, version: int
    ) -> str | None:
        """Look up ``llm_provider`` by ``(system_name, version)`` and return its decrypted API key."""

        with self._session_manager.get_session() as session:
            provider = (
                session.query(LLMProviderModel)
                .filter(
                    LLMProviderModel.system_name == provider_system_name,
                    LLMProviderModel.version == version,
                )
                .first()
            )
            if provider is None:
                return None
            provider_id = int(provider.id)
        return self.get_plain_api_key_for_provider(provider_id)

    def get_plain_api_key_for_provider(self, llm_provider_id: int) -> str | None:
        """Return the decrypted provider API key, or ``None`` if missing or decryption fails."""

        with self._session_manager.get_session() as session:
            rows = (
                session.query(LLMProviderApiKeyModel)
                .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
                .order_by(LLMProviderApiKeyModel.id.asc())
                .all()
            )
            if not rows:
                return None
            row = rows[0]
            if len(rows) > 1:
                logger.warning(
                    "Multiple API key rows for llm_provider_id=%s; using first id=%s",
                    llm_provider_id,
                    row.id,
                )
            # Copy column values before leaving the session (avoid detached-instance errors).
            encrypted_key = row.encrypted_key
            salt = row.salt
            nonce = row.nonce
            authentication_tag = row.authentication_tag

        try:
            master = SecretsMasterKeyService(MoonshotConfigAdapter()).get_or_create_master_key_bytes()
            return decrypt_api_key(
                encrypted_key,
                salt,
                nonce,
                authentication_tag,
                master,
            )
        except (LegacyApiKeyStorageError, SecretDecryptionError, ValueError) as exc:
            logger.warning(
                "Could not decrypt API key for llm_provider_id=%s: %s",
                llm_provider_id,
                exc,
            )
            return None

    def ensure_provider_api_key_in_environment(
        self,
        *,
        llm_provider_id: int,
        adapter_module: str,
    ) -> None:
        env_name = get_adapter_module_to_env().get(adapter_module)
        if env_name is None:
            return

        plain = self.get_plain_api_key_for_provider(llm_provider_id)
        if plain and plain.strip():
            os.environ[env_name] = plain.strip()
            logger.debug(
                "Using API key from database for llm_provider_id=%s (%s)",
                llm_provider_id,
                env_name,
            )
            return

        existing = (os.environ.get(env_name) or "").strip()
        if existing:
            logger.debug(
                "No usable DB API key for llm_provider_id=%s; using existing %s from environment",
                llm_provider_id,
                env_name,
            )
            return

        logger.warning(
            "No API key row for llm_provider_id=%s and %s is unset; connector may fail",
            llm_provider_id,
            env_name,
        )
