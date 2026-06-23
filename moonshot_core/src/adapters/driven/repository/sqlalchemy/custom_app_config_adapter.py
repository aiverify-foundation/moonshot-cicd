"""SQLAlchemy-based implementation of CustomAppConfigRepository."""

from __future__ import annotations

from domain.services.logger import get_logger

from datetime import datetime, timezone
from typing import Dict, List, Optional, override

from sqlalchemy.orm import Session

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    CustomAppConfigModel,
    CustomAppConfigParametersModel,
    CustomAppModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.custom_app_config_repository import CustomAppConfigRepository
from domain.entities.custom_app_config_entity import CustomAppConfigEntity


def _utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CustomAppConfigAdapter(CustomAppConfigRepository):
    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()
        self._logger = get_logger(__name__)

    def _model_to_entity(self, model: CustomAppConfigModel) -> CustomAppConfigEntity:
        return CustomAppConfigEntity(
            id=model.id,
            custom_app_id=model.custom_app_id,
            name=model.name,
            update_dt=model.update_dt,
        )

    def _ensure_app_exists(self, session: Session, custom_app_id: int) -> None:
        app = (
            session.query(CustomAppModel)
            .filter(CustomAppModel.id == custom_app_id)
            .first()
        )
        if app is None:
            raise ValueError(f"No custom_app with id={custom_app_id}")

    def _replace_parameters(
        self, session: Session, config_id: int, parameters: Dict[str, str]
    ) -> None:
        session.query(CustomAppConfigParametersModel).filter(
            CustomAppConfigParametersModel.config_id == config_id
        ).delete(synchronize_session=False)
        for key, value in parameters.items():
            session.add(
                CustomAppConfigParametersModel(
                    config_id=config_id,
                    key=key,
                    value=str(value),
                )
            )

    @override
    def get_by_id(self, config_id: int) -> Optional[CustomAppConfigEntity]:
        with self._session_manager.get_session() as session:
            model = (
                session.query(CustomAppConfigModel)
                .filter(CustomAppConfigModel.id == config_id)
                .first()
            )
            return self._model_to_entity(model) if model else None

    @override
    def list_by_app_id(self, custom_app_id: int) -> List[CustomAppConfigEntity]:
        with self._session_manager.get_session() as session:
            models = (
                session.query(CustomAppConfigModel)
                .filter(CustomAppConfigModel.custom_app_id == custom_app_id)
                .order_by(CustomAppConfigModel.name)
                .all()
            )
            return [self._model_to_entity(m) for m in models]

    @override
    def get_parameters(self, config_id: int) -> Dict[str, str]:
        with self._session_manager.get_session() as session:
            rows = (
                session.query(CustomAppConfigParametersModel)
                .filter(CustomAppConfigParametersModel.config_id == config_id)
                .all()
            )
            return {str(r.key): str(r.value) for r in rows}

    @override
    def create(
        self,
        custom_app_id: int,
        name: str,
        parameters: Dict[str, str],
    ) -> CustomAppConfigEntity:
        with self._session_manager.get_session() as session:
            self._ensure_app_exists(session, custom_app_id)
            cfg = CustomAppConfigModel(
                custom_app_id=custom_app_id,
                name=name,
                update_dt=_utc_naive_now(),
            )
            session.add(cfg)
            session.flush()
            cid = int(cfg.id)
            self._replace_parameters(session, cid, parameters)
            self._logger.info(
                "Created custom_app_config id=%s custom_app_id=%s name=%r",
                cid,
                custom_app_id,
                name,
            )
            return self._model_to_entity(cfg)

    @override
    def update(
        self,
        config_id: int,
        name: str,
        parameters: Dict[str, str],
    ) -> CustomAppConfigEntity:
        with self._session_manager.get_session() as session:
            cfg = (
                session.query(CustomAppConfigModel)
                .filter(CustomAppConfigModel.id == config_id)
                .first()
            )
            if cfg is None:
                raise ValueError(f"No custom_app_config with id={config_id}")
            cfg.name = name
            cfg.update_dt = _utc_naive_now()
            self._replace_parameters(session, config_id, parameters)
            session.flush()
            self._logger.info("Updated custom_app_config id=%s name=%r", config_id, name)
            return self._model_to_entity(cfg)
