"""SQLAlchemy implementation of CustomAppConfigSecretRepository."""

from __future__ import annotations

from domain.services.logger import get_logger

from typing import List, override

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    CustomAppConfigSecretsModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.custom_app_config_secret_repository import (
    CustomAppConfigSecretConflictError,
    CustomAppConfigSecretNotFoundError,
    CustomAppConfigSecretRepository,
)
from domain.services.secret_encryption import EncryptedApiKeyFields


class CustomAppConfigSecretAdapter(CustomAppConfigSecretRepository):
    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()
        self._logger = get_logger(__name__)

    def _row_to_fields(self, row: CustomAppConfigSecretsModel) -> EncryptedApiKeyFields:
        return EncryptedApiKeyFields(
            encrypted_key=row.encrypted_secret,
            salt=row.salt,
            nonce=row.nonce,
            authentication_tag=row.authentication_tag,
        )

    def _get_row(
        self, session, config_id: int, key: str
    ) -> CustomAppConfigSecretsModel | None:
        return (
            session.query(CustomAppConfigSecretsModel)
            .filter(
                CustomAppConfigSecretsModel.config_id == config_id,
                CustomAppConfigSecretsModel.key == key,
            )
            .first()
        )

    @override
    def insert(self, config_id: int, key: str, payload: EncryptedApiKeyFields) -> None:
        with self._session_manager.get_session() as session:
            if self._get_row(session, config_id, key) is not None:
                raise CustomAppConfigSecretConflictError(
                    f"Secret already exists for config_id={config_id} key={key!r}"
                )
            session.add(
                CustomAppConfigSecretsModel(
                    config_id=config_id,
                    key=key,
                    encrypted_secret=payload.encrypted_key,
                    salt=payload.salt,
                    nonce=payload.nonce,
                    authentication_tag=payload.authentication_tag,
                )
            )

    @override
    def update(self, config_id: int, key: str, payload: EncryptedApiKeyFields) -> None:
        with self._session_manager.get_session() as session:
            row = self._get_row(session, config_id, key)
            if row is None:
                raise CustomAppConfigSecretNotFoundError(
                    f"No secret for config_id={config_id} key={key!r}"
                )
            row.encrypted_secret = payload.encrypted_key
            row.salt = payload.salt
            row.nonce = payload.nonce
            row.authentication_tag = payload.authentication_tag

    @override
    def replace(self, config_id: int, key: str, payload: EncryptedApiKeyFields) -> None:
        with self._session_manager.get_session() as session:
            session.query(CustomAppConfigSecretsModel).filter(
                CustomAppConfigSecretsModel.config_id == config_id,
                CustomAppConfigSecretsModel.key == key,
            ).delete(synchronize_session=False)
            session.add(
                CustomAppConfigSecretsModel(
                    config_id=config_id,
                    key=key,
                    encrypted_secret=payload.encrypted_key,
                    salt=payload.salt,
                    nonce=payload.nonce,
                    authentication_tag=payload.authentication_tag,
                )
            )

    @override
    def get_encrypted(self, config_id: int, key: str) -> EncryptedApiKeyFields:
        with self._session_manager.get_session() as session:
            row = self._get_row(session, config_id, key)
            if row is None:
                raise CustomAppConfigSecretNotFoundError(
                    f"No secret for config_id={config_id} key={key!r}"
                )
            return self._row_to_fields(row)

    @override
    def list_keys(self, config_id: int) -> List[str]:
        with self._session_manager.get_session() as session:
            rows = (
                session.query(CustomAppConfigSecretsModel)
                .filter(CustomAppConfigSecretsModel.config_id == config_id)
                .order_by(CustomAppConfigSecretsModel.key)
                .all()
            )
            return [str(r.key) for r in rows]
