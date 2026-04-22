"""SQLAlchemy implementation of LlmProviderApiKeyRepository."""

from __future__ import annotations

from typing import override

from adapters.driven.repository.sqlalchemy.llm_provider_models import LLMProviderApiKeyModel
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.llm_provider_api_key_repository import (
    LlmProviderApiKeyAmbiguousError,
    LlmProviderApiKeyConflictError,
    LlmProviderApiKeyNotFoundError,
    LlmProviderApiKeyRepository,
)
from domain.services.logger import configure_logger
from domain.services.secret_encryption import EncryptedApiKeyFields


class LLMProviderApiKeyAdapter(LlmProviderApiKeyRepository):
    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()
        self._logger = configure_logger(__name__)

    def _rows_for_provider(self, session, llm_provider_id: int) -> list[LLMProviderApiKeyModel]:
        return (
            session.query(LLMProviderApiKeyModel)
            .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
            .order_by(LLMProviderApiKeyModel.id.asc())
            .all()
        )

    @override
    def insert(self, llm_provider_id: int, payload: EncryptedApiKeyFields) -> None:
        with self._session_manager.get_session() as session:
            rows = self._rows_for_provider(session, llm_provider_id)
            if len(rows) > 0:
                self._logger.warning(
                    "insert refused: %s row(s) already exist for llm_provider_id=%s",
                    len(rows),
                    llm_provider_id,
                )
                raise LlmProviderApiKeyConflictError(
                    f"API key already exists for llm_provider_id={llm_provider_id}"
                )
            row = LLMProviderApiKeyModel(
                llm_provider_id=llm_provider_id,
                encrypted_key=payload.encrypted_key,
                salt=payload.salt,
                nonce=payload.nonce,
                authentication_tag=payload.authentication_tag,
            )
            session.add(row)

    @override
    def update(self, llm_provider_id: int, payload: EncryptedApiKeyFields) -> None:
        with self._session_manager.get_session() as session:
            rows = self._rows_for_provider(session, llm_provider_id)
            if len(rows) == 0:
                raise LlmProviderApiKeyNotFoundError(
                    f"No API key for llm_provider_id={llm_provider_id}"
                )
            if len(rows) > 1:
                raise LlmProviderApiKeyAmbiguousError(
                    f"Multiple API key rows ({len(rows)}) for llm_provider_id={llm_provider_id}"
                )
            row = rows[0]
            row.encrypted_key = payload.encrypted_key
            row.salt = payload.salt
            row.nonce = payload.nonce
            row.authentication_tag = payload.authentication_tag

    @override
    def replace(self, llm_provider_id: int, payload: EncryptedApiKeyFields) -> None:
        with self._session_manager.get_session() as session:
            n = (
                session.query(LLMProviderApiKeyModel)
                .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
                .delete(synchronize_session=False)
            )
            if n:
                self._logger.info(
                    "Replaced %s API key row(s) for llm_provider_id=%s",
                    n,
                    llm_provider_id,
                )
            row = LLMProviderApiKeyModel(
                llm_provider_id=llm_provider_id,
                encrypted_key=payload.encrypted_key,
                salt=payload.salt,
                nonce=payload.nonce,
                authentication_tag=payload.authentication_tag,
            )
            session.add(row)
