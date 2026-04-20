"""Ensure connector adapters see an API key: prefer existing env, else DB provider key."""

from __future__ import annotations

import os

from adapters.driven.repository.sqlalchemy.llm_provider_models import LLMProviderApiKeyModel
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import MoonshotConfigAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.secrets_master_key_service import SecretsMasterKeyService
from domain.services.logger import configure_logger
from domain.services.secret_encryption import (
    LegacyApiKeyStorageError,
    SecretDecryptionError,
    decrypt_api_key,
)

logger = configure_logger(__name__)

# Connector module name (same as ModuleLoader / ConnectorEntity) -> env var the adapter reads
ADAPTER_MODULE_TO_ENV: dict[str, str] = {
    "openai_adapter": "OPENAI_API_KEY",
    "together_adapter": "TOGETHER_API_KEY",
}


class ProviderConnectorEnvKeyService:
    """
    When running benchmarks against a DB-resolved connector, adapters read API keys from
    os.environ. This service fills that env var only when needed:

    - If the env var for the adapter is already set and non-empty, does nothing (keeps the
      existing key, e.g. from the shell or CI).
    - Otherwise, if an llm_provider_api_key row exists for the provider, decrypts it and
      sets the env var so the connector can authenticate.
    """

    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()

    def ensure_provider_api_key_in_environment(
        self,
        *,
        llm_provider_id: int,
        adapter_module: str,
    ) -> None:
        env_name = ADAPTER_MODULE_TO_ENV.get(adapter_module)
        if env_name is None:
            return
        existing = (os.environ.get(env_name) or "").strip()
        if existing:
            logger.debug(
                "Using existing %s from environment for llm_provider_id=%s",
                env_name,
                llm_provider_id,
            )
            return

        with self._session_manager.get_session() as session:
            rows = (
                session.query(LLMProviderApiKeyModel)
                .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
                .order_by(LLMProviderApiKeyModel.id.asc())
                .all()
            )
        if not rows:
            logger.warning(
                "No API key row for llm_provider_id=%s and %s is unset; connector may fail",
                llm_provider_id,
                env_name,
            )
            return
        row = rows[0]
        if len(rows) > 1:
            logger.warning(
                "Multiple API key rows for llm_provider_id=%s; using first id=%s",
                llm_provider_id,
                row.id,
            )
        try:
            master = SecretsMasterKeyService(MoonshotConfigAdapter()).get_or_create_master_key_bytes()
            plain = decrypt_api_key(
                row.encrypted_key,
                row.salt,
                row.nonce,
                row.authentication_tag,
                master,
            )
        except (LegacyApiKeyStorageError, SecretDecryptionError, ValueError) as exc:
            logger.warning(
                "Could not decrypt API key for llm_provider_id=%s: %s",
                llm_provider_id,
                exc,
            )
            return
        os.environ[env_name] = plain
