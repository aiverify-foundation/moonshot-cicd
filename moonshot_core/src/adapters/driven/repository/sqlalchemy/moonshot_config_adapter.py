"""SQLAlchemy-based implementation of MoonshotConfigRepository."""

from typing import Dict, Optional, override

from application.ports.moonshot_config_repository import MoonshotConfigRepository
from domain.entities.moonshot_config_entity import MoonshotConfigEntity
from domain.services.logger import configure_logger
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.llm_provider_models import MoonshotConfigModel


class MoonshotConfigAdapter(MoonshotConfigRepository):
    """SQLAlchemy adapter for moonshot_config table (key-value application config)."""

    def __init__(self) -> None:
        self.session_manager = SessionManager.get_instance()
        self.logger = configure_logger(__name__)

    def _model_to_entity(self, model: MoonshotConfigModel) -> MoonshotConfigEntity:
        return MoonshotConfigEntity(id=model.id, key=model.key, value=model.value)

    @override
    def get_by_key(self, key: str) -> Optional[MoonshotConfigEntity]:
        try:
            with self.session_manager.get_session() as session:
                model = (
                    session.query(MoonshotConfigModel).filter(MoonshotConfigModel.key == key).first()
                )
                return self._model_to_entity(model) if model else None
        except Exception as e:
            self.logger.error("MoonshotConfigAdapter.get_by_key error: %s", e)
            raise

    @override
    def set(self, key: str, value: str | None) -> MoonshotConfigEntity:
        try:
            with self.session_manager.get_session() as session:
                model = (
                    session.query(MoonshotConfigModel).filter(MoonshotConfigModel.key == key).first()
                )
                if model:
                    model.value = value
                    session.flush()
                    return self._model_to_entity(model)
                new_model = MoonshotConfigModel(key=key, value=value)
                session.add(new_model)
                session.flush()
                return self._model_to_entity(new_model)
        except Exception as e:
            self.logger.error("MoonshotConfigAdapter.set error: %s", e)
            raise

    @override
    def get_all(self) -> Dict[str, str | None]:
        try:
            with self.session_manager.get_session() as session:
                models = session.query(MoonshotConfigModel).all()
                return {m.key: m.value for m in models}
        except Exception as e:
            self.logger.error("MoonshotConfigAdapter.get_all error: %s", e)
            raise

    @override
    def delete_by_key(self, key: str) -> bool:
        try:
            with self.session_manager.get_session() as session:
                model = (
                    session.query(MoonshotConfigModel).filter(MoonshotConfigModel.key == key).first()
                )
                if model:
                    session.delete(model)
                    return True
                return False
        except Exception as e:
            self.logger.error("MoonshotConfigAdapter.delete_by_key error: %s", e)
            raise
