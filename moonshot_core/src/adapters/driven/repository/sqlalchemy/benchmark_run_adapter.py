"""SQLAlchemy-based implementation of BenchmarkRunRepository."""

from domain.services.logger import get_logger

from datetime import datetime, timezone
from typing import Optional, override

from adapters.driven.repository.sqlalchemy.llm_provider_models import \
    BenchmarkRunModel
from adapters.driven.repository.sqlalchemy.session_manager import \
    SessionManager
from application.ports.benchmark_run_repository import BenchmarkRunRepository
from domain.entities.benchmark_run_entity import BenchmarkRunEntity


class SqlAlchemyBenchmarkRunRepository(BenchmarkRunRepository):
    """
    SQLAlchemy-based implementation of BenchmarkRunRepository.

    Uses BenchmarkRunModel and SessionManager for DB access.
    """

    def __init__(self):
        self.session_manager = SessionManager.get_instance()
        self.logger = get_logger(__name__)

    def _model_to_entity(self, model: BenchmarkRunModel) -> BenchmarkRunEntity:
        """Map BenchmarkRunModel to BenchmarkRunEntity."""
        return BenchmarkRunEntity(
            id=model.id,
            name=model.name,
            status=model.status,
            endpoint_type=model.endpoint_type,
            start_time=model.start_time,
            end_time=model.end_time,
            llm_provider_id=model.llm_provider_id,
            llm_provider_model_id=model.llm_provider_model_id,
            llm_provider_model_config_id=model.llm_provider_model_config_id,
            custom_app_id=model.custom_app_id,
            custom_app_config_id=model.custom_app_config_id,
        )

    @override
    def get_by_id(self, run_id: int) -> Optional[BenchmarkRunEntity]:
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunModel)
                .filter(BenchmarkRunModel.id == run_id)
                .first()
            )
            return self._model_to_entity(model) if model else None

    @override
    def get_by_name(self, name: str) -> Optional[BenchmarkRunEntity]:
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunModel)
                .filter(BenchmarkRunModel.name == name)
                .first()
            )
            return self._model_to_entity(model) if model else None

    @override
    def get_all(self) -> list[BenchmarkRunEntity]:
        with self.session_manager.get_session() as session:
            models = session.query(BenchmarkRunModel).all()
            return [self._model_to_entity(m) for m in models]

    @override
    def save(self, entity: BenchmarkRunEntity) -> BenchmarkRunEntity:
        """Insert only. Entity must not have id set."""
        if entity.id is not None and entity.id != 0:
            raise ValueError(
                "Cannot save: entity has id set. Use update() for existing runs."
            )
        with self.session_manager.get_session() as session:
            model = BenchmarkRunModel(
                name=entity.name,
                status=entity.status,
                endpoint_type=entity.endpoint_type,
                start_time=entity.start_time or datetime.now(timezone.utc),
                end_time=entity.end_time,
                llm_provider_id=entity.llm_provider_id,
                llm_provider_model_id=entity.llm_provider_model_id,
                llm_provider_model_config_id=entity.llm_provider_model_config_id,
                custom_app_id=entity.custom_app_id,
                custom_app_config_id=entity.custom_app_config_id,
            )
            session.add(model)
            session.flush()
            return self._model_to_entity(model)

    @override
    def update(self, entity: BenchmarkRunEntity) -> BenchmarkRunEntity:
        with self.session_manager.get_session() as session:
            if entity.id is None or entity.id == 0:
                raise ValueError("Cannot update: entity must have id set")
            model = (
                session.query(BenchmarkRunModel)
                .filter(BenchmarkRunModel.id == entity.id)
                .first()
            )
            if model is None:
                raise ValueError(
                    f"Cannot update: no benchmark_run with id={entity.id}"
                )
            model.name = entity.name
            model.status = entity.status
            model.endpoint_type = entity.endpoint_type
            model.start_time = entity.start_time
            model.end_time = entity.end_time
            model.llm_provider_id = entity.llm_provider_id
            model.llm_provider_model_id = entity.llm_provider_model_id
            model.llm_provider_model_config_id = entity.llm_provider_model_config_id
            model.custom_app_id = entity.custom_app_id
            model.custom_app_config_id = entity.custom_app_config_id
            session.flush()
            return self._model_to_entity(model)
