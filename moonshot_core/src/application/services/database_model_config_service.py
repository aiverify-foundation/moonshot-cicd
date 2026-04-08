"""Create/update llm_provider_model_config and parameter rows (relational DB only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelModel,
    LLMProviderEndpointConfigParametersModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.dto.model_config_dto import (
    CreateDatabaseModelConfigBody,
    ModelConfigDTO,
    UpdateDatabaseModelConfigBody,
)
from domain.services.logger import configure_logger


class DatabaseModelConfigNotFoundError(Exception):
    """No llm_provider_model_config row for the given id."""


class DatabaseModelConfigConflictError(Exception):
    """Unique constraint violation or duplicate (model_id, name)."""


class DatabaseModelConfigBadRequestError(Exception):
    """Invalid model_id or request payload."""


def _utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DatabaseModelConfigService:
    """Insert and update database-backed LLM provider model configs (not SQLite legacy store)."""

    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()
        self._logger = configure_logger(__name__)

    def create(self, body: CreateDatabaseModelConfigBody) -> ModelConfigDTO:
        self._logger.info(
            "Creating database model config model_id=%s name=%r", body.model_id, body.name
        )
        try:
            with self._session_manager.get_session() as session:
                self._ensure_model_exists(session, body.model_id)
                if self._config_exists(session, body.model_id, body.name):
                    raise DatabaseModelConfigConflictError(
                        f"Model config already exists for model_id={body.model_id} "
                        f"name={body.name!r}"
                    )
                now = _utc_naive_now()
                cfg = LLMProviderModelConfigModel(
                    model_id=body.model_id,
                    name=body.name,
                    updated_dt=now,
                    last_used_dt=body.last_used_dt,
                )
                session.add(cfg)
                session.flush()
                cid = int(cfg.id)
                self._replace_parameters(session, cid, body.savedConfigPairs)
                return self._to_model_config_dto(session, cid)
        except IntegrityError as exc:
            raise DatabaseModelConfigConflictError(
                "Database constraint violation while creating model config"
            ) from exc

    def update(self, config_id: int, body: UpdateDatabaseModelConfigBody) -> ModelConfigDTO:
        self._logger.info(
            "Updating database model config id=%s model_id=%s name=%r",
            config_id,
            body.model_id,
            body.name,
        )
        try:
            with self._session_manager.get_session() as session:
                cfg = (
                    session.query(LLMProviderModelConfigModel)
                    .filter(LLMProviderModelConfigModel.id == config_id)
                    .first()
                )
                if cfg is None:
                    raise DatabaseModelConfigNotFoundError(
                        f"No model config with id={config_id}"
                    )
                self._ensure_model_exists(session, body.model_id)
                other = (
                    session.query(LLMProviderModelConfigModel)
                    .filter(
                        LLMProviderModelConfigModel.model_id == body.model_id,
                        LLMProviderModelConfigModel.name == body.name,
                        LLMProviderModelConfigModel.id != config_id,
                    )
                    .first()
                )
                if other is not None:
                    raise DatabaseModelConfigConflictError(
                        f"Another config already uses model_id={body.model_id} name={body.name!r}"
                    )
                cfg.name = body.name
                cfg.model_id = body.model_id
                cfg.updated_dt = _utc_naive_now()
                if body.last_used_dt is not None:
                    cfg.last_used_dt = body.last_used_dt
                self._replace_parameters(session, config_id, body.savedConfigPairs)
                return self._to_model_config_dto(session, config_id)
        except IntegrityError as exc:
            raise DatabaseModelConfigConflictError(
                "Database constraint violation while updating model config"
            ) from exc

    def _ensure_model_exists(self, session: Session, model_id: int) -> None:
        exists = (
            session.query(LLMProviderModelModel)
            .filter(LLMProviderModelModel.id == model_id)
            .first()
        )
        if exists is None:
            raise DatabaseModelConfigBadRequestError(
                f"No llm_provider_model with id={model_id}"
            )

    def _config_exists(self, session: Session, model_id: int, name: str) -> bool:
        return (
            session.query(LLMProviderModelConfigModel)
            .filter(
                LLMProviderModelConfigModel.model_id == model_id,
                LLMProviderModelConfigModel.name == name,
            )
            .first()
            is not None
        )

    def _replace_parameters(
        self, session: Session, config_id: int, pairs: Dict[str, str]
    ) -> None:
        session.query(LLMProviderEndpointConfigParametersModel).filter(
            LLMProviderEndpointConfigParametersModel.config_id == config_id
        ).delete(synchronize_session=False)
        for key, value in pairs.items():
            session.add(
                LLMProviderEndpointConfigParametersModel(
                    config_id=config_id,
                    key=key,
                    value=str(value),
                )
            )

    def _to_model_config_dto(self, session: Session, config_id: int) -> ModelConfigDTO:
        row = (
            session.query(LLMProviderModelConfigModel)
            .filter(LLMProviderModelConfigModel.id == config_id)
            .first()
        )
        if row is None:
            raise DatabaseModelConfigNotFoundError(
                f"No model config with id={config_id}"
            )
        mid = row.model_id
        if mid is None:
            raise DatabaseModelConfigBadRequestError(
                f"Model config id={config_id} has null model_id"
            )
        model_row = (
            session.query(LLMProviderModelModel)
            .filter(LLMProviderModelModel.id == int(mid))
            .first()
        )
        if model_row is None:
            raise DatabaseModelConfigBadRequestError(
                f"llm_provider_model id={mid} missing for config id={config_id}"
            )
        provider = (
            session.query(LLMProviderModel)
            .filter(LLMProviderModel.id == model_row.llm_provider_id)
            .first()
        )
        if provider is None:
            raise DatabaseModelConfigBadRequestError(
                f"llm_provider id={model_row.llm_provider_id} missing for config id={config_id}"
            )
        param_rows = (
            session.query(LLMProviderEndpointConfigParametersModel)
            .filter(
                LLMProviderEndpointConfigParametersModel.config_id == config_id,
            )
            .all()
        )
        pairs = {str(p.key): str(p.value) for p in param_rows}
        return ModelConfigDTO(
            id=str(config_id),
            name=str(row.name),
            modelname=str(model_row.name),
            providerID=str(provider.system_name),
            savedConfigPairs=pairs,
            lastUpdated=row.updated_dt,
        )
