"""Create/update encrypted secrets for custom_app_config rows."""

from __future__ import annotations

from domain.services.logger import get_logger

from adapters.driven.repository.sqlalchemy.custom_app_config_adapter import (
    CustomAppConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.custom_app_config_secret_adapter import (
    CustomAppConfigSecretAdapter,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import MoonshotConfigAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.custom_app_config_repository import CustomAppConfigRepository
from application.ports.custom_app_config_secret_repository import (
    CustomAppConfigSecretRepository,
)
from application.services.secrets_master_key_service import SecretsMasterKeyService
from domain.services.secret_encryption import (
    EncryptedApiKeyFields,
    LegacyApiKeyStorageError,
    decrypt_api_key,
    encrypt_api_key,
)


class CustomAppConfigSecretUnknownConfigError(Exception):
    """No custom_app_config row for the given id."""


class CustomAppConfigSecretService:
    def __init__(
        self,
        secret_repository: CustomAppConfigSecretRepository | None = None,
        config_repository: CustomAppConfigRepository | None = None,
        session_manager: SessionManager | None = None,
        secrets_master_key: SecretsMasterKeyService | None = None,
    ) -> None:
        self._secret_repository = secret_repository or CustomAppConfigSecretAdapter(
            session_manager
        )
        self._config_repository = config_repository or CustomAppConfigAdapter(session_manager)
        self._secrets_master_key = secrets_master_key or SecretsMasterKeyService(
            MoonshotConfigAdapter()
        )
        self._logger = get_logger(__name__)

    def _ensure_config_exists(self, config_id: int) -> None:
        if self._config_repository.get_by_id(config_id) is None:
            raise CustomAppConfigSecretUnknownConfigError(
                f"No custom_app_config with id={config_id}"
            )

    def _encrypt(self, plaintext: str) -> EncryptedApiKeyFields:
        master = self._secrets_master_key.get_or_create_master_key_bytes()
        return encrypt_api_key(plaintext, master)

    def set_secret(self, config_id: int, key: str, plaintext: str) -> None:
        if not plaintext:
            raise ValueError("secret must be non-empty")
        if not key.strip():
            raise ValueError("key must be non-empty")
        self._ensure_config_exists(config_id)
        self._logger.info(
            "Setting secret for custom_app_config_id=%s key=%r", config_id, key
        )
        self._secret_repository.replace(config_id, key.strip(), self._encrypt(plaintext))

    def get_decrypted_secret(self, config_id: int, key: str) -> str:
        self._ensure_config_exists(config_id)
        fields = self._secret_repository.get_encrypted(config_id, key)
        master = self._secrets_master_key.get_or_create_master_key_bytes()
        try:
            return decrypt_api_key(
                fields.encrypted_key,
                fields.salt,
                fields.nonce,
                fields.authentication_tag,
                master,
            )
        except LegacyApiKeyStorageError:
            raise

    def get_all_decrypted_secrets(self, config_id: int) -> dict[str, str]:
        self._ensure_config_exists(config_id)
        result: dict[str, str] = {}
        for key in self._secret_repository.list_keys(config_id):
            result[key] = self.get_decrypted_secret(config_id, key)
        return result

    def is_secret_configured(self, config_id: int, key: str = "api_key") -> bool:
        """True if an encrypted secret row exists for config_id and key (no decryption)."""
        return key in self._secret_repository.list_keys(config_id)
