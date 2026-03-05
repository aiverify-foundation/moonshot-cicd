"""SQLAlchemy-based implementation of BenchmarkRunTestStatusRepository."""

from typing import Optional, override

from adapters.driven.repository.sqlalchemy.llm_provider_models import \
    BenchmarkRunTestStatusModel
from adapters.driven.repository.sqlalchemy.session_manager import \
    SessionManager
from application.ports.benchmark_run_test_status_repository import \
    BenchmarkRunTestStatusRepository
from domain.entities.benchmark_run_test_status_entity import \
    BenchmarkRunTestStatusEntity
from domain.services.logger import configure_logger


class SqlAlchemyBenchmarkRunTestStatusRepository(BenchmarkRunTestStatusRepository):
    """
    SQLAlchemy-based implementation of BenchmarkRunTestStatusRepository.

    Uses BenchmarkRunTestStatusModel and SessionManager for DB access.
    """

    def __init__(self):
        self.session_manager = SessionManager.get_instance()
        self.logger = configure_logger(__name__)

    def _model_to_entity(
        self, model: BenchmarkRunTestStatusModel
    ) -> BenchmarkRunTestStatusEntity:
        """Map BenchmarkRunTestStatusModel to BenchmarkRunTestStatusEntity."""
        return BenchmarkRunTestStatusEntity(
            id=model.id,
            run_id=model.run_id,
            test_id=model.test_id,
            status=model.status,
            start_dt=model.start_dt,
            end_dt=model.end_dt,
            connector_pre_prompt=model.connector_pre_prompt,
            connector_post_prompt=model.connector_post_prompt,
            system_prompt=model.system_prompt,
        )

    @override
    def get_by_id(
        self, run_test_status_id: int
    ) -> Optional[BenchmarkRunTestStatusEntity]:
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunTestStatusModel)
                .filter(BenchmarkRunTestStatusModel.id == run_test_status_id)
                .first()
            )
            return self._model_to_entity(model) if model else None

    @override
    def get_all_by_run_id(self, run_id: int) -> list[BenchmarkRunTestStatusEntity]:
        with self.session_manager.get_session() as session:
            models = (
                session.query(BenchmarkRunTestStatusModel)
                .filter(BenchmarkRunTestStatusModel.run_id == run_id)
                .all()
            )
            return [self._model_to_entity(m) for m in models]

    @override
    def get_by_run_and_test(
        self, run_id: int, test_id: int
    ) -> Optional[BenchmarkRunTestStatusEntity]:
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunTestStatusModel)
                .filter(
                    BenchmarkRunTestStatusModel.run_id == run_id,
                    BenchmarkRunTestStatusModel.test_id == test_id,
                )
                .first()
            )
            return self._model_to_entity(model) if model else None

    @override
    def save(
        self, entity: BenchmarkRunTestStatusEntity
    ) -> BenchmarkRunTestStatusEntity:
        """Insert only. Entity must not have id set."""
        if entity.id is not None and entity.id != 0:
            raise ValueError(
                "Cannot save: entity has id set. Use update() for existing run test status."
            )
        with self.session_manager.get_session() as session:
            model = BenchmarkRunTestStatusModel(
                run_id=entity.run_id,
                test_id=entity.test_id,
                status=entity.status,
                start_dt=entity.start_dt,
                end_dt=entity.end_dt,
                connector_pre_prompt=entity.connector_pre_prompt,
                connector_post_prompt=entity.connector_post_prompt,
                system_prompt=entity.system_prompt,
            )
            session.add(model)
            session.flush()
            return self._model_to_entity(model)

    @override
    def update(
        self, entity: BenchmarkRunTestStatusEntity
    ) -> BenchmarkRunTestStatusEntity:
        """Update an existing run test status. Entity must have id set."""
        if entity.id is None or entity.id == 0:
            raise ValueError("Cannot update: entity must have id set")
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunTestStatusModel)
                .filter(BenchmarkRunTestStatusModel.id == entity.id)
                .first()
            )
            if model is None:
                raise ValueError(
                    f"Cannot update: no benchmark_run_test_status with id={entity.id}"
                )
            model.run_id = entity.run_id
            model.test_id = entity.test_id
            model.status = entity.status
            model.start_dt = entity.start_dt
            model.end_dt = entity.end_dt
            model.connector_pre_prompt = entity.connector_pre_prompt
            model.connector_post_prompt = entity.connector_post_prompt
            model.system_prompt = entity.system_prompt
            session.flush()
            return self._model_to_entity(model)
