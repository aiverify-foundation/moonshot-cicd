"""Create/update llm_provider_model_config and parameter rows (relational DB only)."""

from __future__ import annotations

from domain.services.logger import get_logger

from datetime import datetime, timezone
from typing import Dict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelConfigParametersModel,
    LLMProviderModelModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.dto.model_config_dto import (
    CreateDatabaseModelConfigBody,
    ModelConfigDTO,
    UpdateDatabaseModelConfigBody,
)


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
        self._logger = get_logger(__name__)

    def create(self, body: CreateDatabaseModelConfigBody) -> tuple[ModelConfigDTO, bool]:
        """
        Insert a new llm_provider_model row (when resolved by provider + name) and a new config.

        Returns (dto, True). Each config owns its model row; model names are not looked up for linking.
        """
        try:
            with self._session_manager.get_session() as session:
                resolved_model_id = self._resolve_model_id_for_create(
                    session,
                    model_id=body.model_id,
                    llm_provider_id=body.llm_provider_id,
                    model_name=body.model_name,
                )
                self._logger.info(
                    "Creating database model config model_id=%s name=%r",
                    resolved_model_id,
                    body.name,
                )
                now = _utc_naive_now()
                cfg = LLMProviderModelConfigModel(
                    model_id=resolved_model_id,
                    name=body.name,
                    updated_dt=now,
                    last_used_dt=body.last_used_dt,
                )
                session.add(cfg)
                session.flush()
                cid = int(cfg.id)
                self._replace_parameters(session, cid, body.savedConfigPairs)
                return self._to_model_config_dto(session, cid), True
        except IntegrityError as exc:
            raise DatabaseModelConfigConflictError(
                "Database constraint violation while creating model config"
            ) from exc

    def _create_llm_provider_model(
        self, session: Session, llm_provider_id: int, model_name: str
    ) -> int:
        provider = (
            session.query(LLMProviderModel)
            .filter(LLMProviderModel.id == llm_provider_id)
            .first()
        )
        if provider is None:
            raise DatabaseModelConfigBadRequestError(
                f"No llm_provider with id={llm_provider_id}"
            )
        row = LLMProviderModelModel(
            llm_provider_id=llm_provider_id,
            name=model_name,
        )
        session.add(row)
        session.flush()
        return int(row.id)

    def update(self, config_id: int, body: UpdateDatabaseModelConfigBody) -> ModelConfigDTO:
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
                linked_model_id = cfg.model_id
                if linked_model_id is None:
                    raise DatabaseModelConfigBadRequestError(
                        f"Model config id={config_id} has null model_id"
                    )
                linked_model_id = int(linked_model_id)

                if body.model_id is not None and int(body.model_id) != linked_model_id:
                    raise DatabaseModelConfigBadRequestError(
                        f"model_id={body.model_id} does not match config's model_id={linked_model_id}"
                    )

                model_row = (
                    session.query(LLMProviderModelModel)
                    .filter(LLMProviderModelModel.id == linked_model_id)
                    .first()
                )
                if model_row is None:
                    raise DatabaseModelConfigBadRequestError(
                        f"No llm_provider_model with id={linked_model_id}"
                    )

                if body.llm_provider_id is not None:
                    if int(body.llm_provider_id) != int(model_row.llm_provider_id):
                        raise DatabaseModelConfigBadRequestError(
                            f"llm_provider_id={body.llm_provider_id} does not match "
                            f"config's provider id={model_row.llm_provider_id}"
                        )
                    if body.model_name is None or not body.model_name.strip():
                        raise DatabaseModelConfigBadRequestError(
                            "model_name must be non-empty when using llm_provider_id"
                        )
                    model_row.name = body.model_name.strip()

                self._logger.info(
                    "Updating database model config id=%s model_id=%s name=%r",
                    config_id,
                    linked_model_id,
                    body.name,
                )
                other = (
                    session.query(LLMProviderModelConfigModel)
                    .filter(
                        LLMProviderModelConfigModel.model_id == linked_model_id,
                        LLMProviderModelConfigModel.name == body.name,
                        LLMProviderModelConfigModel.id != config_id,
                    )
                    .first()
                )
                if other is not None:
                    raise DatabaseModelConfigConflictError(
                        f"Another config already uses model_id={linked_model_id} name={body.name!r}"
                    )

                cfg.name = body.name
                cfg.updated_dt = _utc_naive_now()
                if body.last_used_dt is not None:
                    cfg.last_used_dt = body.last_used_dt
                self._replace_parameters(session, config_id, body.savedConfigPairs)
                return self._to_model_config_dto(session, config_id)
        except IntegrityError as exc:
            raise DatabaseModelConfigConflictError(
                "Database constraint violation while updating model config"
            ) from exc

    def _resolve_model_id_for_create(
        self,
        session: Session,
        *,
        model_id: int | None,
        llm_provider_id: int | None,
        model_name: str | None,
    ) -> int:
        if model_id is not None:
            resolved_model_id = int(model_id)
            self._ensure_model_exists(session, resolved_model_id)
            return resolved_model_id
        if llm_provider_id is None or model_name is None:
            raise DatabaseModelConfigBadRequestError(
                "llm_provider_id and model_name are required when model_id is omitted"
            )
        return self._create_llm_provider_model(
            session,
            int(llm_provider_id),
            model_name.strip(),
        )

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

    def _replace_parameters(
        self, session: Session, config_id: int, pairs: Dict[str, str]
    ) -> None:
        session.query(LLMProviderModelConfigParametersModel).filter(
            LLMProviderModelConfigParametersModel.config_id == config_id
        ).delete(synchronize_session=False)
        for key, value in pairs.items():
            session.add(
                LLMProviderModelConfigParametersModel(
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
            session.query(LLMProviderModelConfigParametersModel)
            .filter(
                LLMProviderModelConfigParametersModel.config_id == config_id,
            )
            .all()
        )
        pairs = {str(p.key): str(p.value) for p in param_rows}
        return ModelConfigDTO(
            id=str(config_id),
            name=str(row.name),
            modelname=str(model_row.name),
            modelId=int(model_row.id),
            providerID=str(provider.system_name),
            savedConfigPairs=pairs,
            lastUpdated=row.updated_dt,
        )
