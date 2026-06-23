"""SQLAlchemy-based implementation of CustomAppRepository."""

from __future__ import annotations

from domain.services.logger import get_logger

from typing import List, Optional, override

from adapters.driven.repository.sqlalchemy.llm_provider_models import CustomAppModel
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.custom_app_repository import CustomAppRepository
from domain.entities.custom_app_entity import CustomAppEntity


class CustomAppAdapter(CustomAppRepository):
    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()
        self._logger = get_logger(__name__)

    def _model_to_entity(self, model: CustomAppModel) -> CustomAppEntity:
        return CustomAppEntity(id=model.id, name=model.name)

    @override
    def get_by_id(self, app_id: int) -> Optional[CustomAppEntity]:
        with self._session_manager.get_session() as session:
            model = (
                session.query(CustomAppModel)
                .filter(CustomAppModel.id == app_id)
                .first()
            )
            return self._model_to_entity(model) if model else None

    @override
    def list_all(self) -> List[CustomAppEntity]:
        with self._session_manager.get_session() as session:
            models = session.query(CustomAppModel).order_by(CustomAppModel.name).all()
            return [self._model_to_entity(m) for m in models]

    @override
    def add(self, name: str) -> CustomAppEntity:
        with self._session_manager.get_session() as session:
            existing = (
                session.query(CustomAppModel)
                .filter(CustomAppModel.name == name)
                .first()
            )
            if existing:
                self._logger.warning("Custom app with name=%r already exists", name)
                return self._model_to_entity(existing)
            model = CustomAppModel(name=name)
            session.add(model)
            session.flush()
            self._logger.info("Added custom app: %s", model)
            return self._model_to_entity(model)
