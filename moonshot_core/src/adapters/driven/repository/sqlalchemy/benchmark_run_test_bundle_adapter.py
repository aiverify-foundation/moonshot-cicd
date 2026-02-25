"""SQLAlchemy-based implementation of BenchmarkRunTestBundleRepository."""

from typing import Optional, override

from adapters.driven.repository.sqlalchemy.llm_provider_models import \
    BenchmarkRunTestBundleModel
from adapters.driven.repository.sqlalchemy.session_manager import \
    SessionManager
from application.ports.benchmark_run_test_bundle_repository import \
    BenchmarkRunTestBundleRepository
from domain.entities.benchmark_run_test_bundle_entity import \
    BenchmarkRunTestBundleEntity
from domain.services.logger import configure_logger


class SqlAlchemyBenchmarkRunTestBundleRepository(BenchmarkRunTestBundleRepository):
    """
    SQLAlchemy-based implementation of BenchmarkRunTestBundleRepository.

    Uses BenchmarkRunTestBundleModel and SessionManager for DB access.
    """

    def __init__(self):
        self.session_manager = SessionManager.get_instance()
        self.logger = configure_logger(__name__)

    def _model_to_entity(
        self, model: BenchmarkRunTestBundleModel
    ) -> BenchmarkRunTestBundleEntity:
        """Map BenchmarkRunTestBundleModel to BenchmarkRunTestBundleEntity."""
        return BenchmarkRunTestBundleEntity(
            id=model.id,
            run_id=model.run_id,
            test_bundle_id=model.test_bundle_id,
            test_id=model.test_id,
        )

    @override
    def get_by_id(
        self, run_test_bundle_id: int
    ) -> Optional[BenchmarkRunTestBundleEntity]:
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunTestBundleModel)
                .filter(BenchmarkRunTestBundleModel.id == run_test_bundle_id)
                .first()
            )
            return self._model_to_entity(model) if model else None

    @override
    def get_all_by_run_id(self, run_id: int) -> list[BenchmarkRunTestBundleEntity]:
        with self.session_manager.get_session() as session:
            models = (
                session.query(BenchmarkRunTestBundleModel)
                .filter(BenchmarkRunTestBundleModel.run_id == run_id)
                .all()
            )
            return [self._model_to_entity(m) for m in models]

    @override
    def save(
        self, entity: BenchmarkRunTestBundleEntity
    ) -> BenchmarkRunTestBundleEntity:
        """Insert only. Entity must not have id set."""
        if entity.id is not None and entity.id != 0:
            raise ValueError(
                "Cannot save: entity has id set. Use update() for existing run test bundle."
            )
        with self.session_manager.get_session() as session:
            model = BenchmarkRunTestBundleModel(
                run_id=entity.run_id,
                test_bundle_id=entity.test_bundle_id,
                test_id=entity.test_id,
            )
            session.add(model)
            session.flush()
            return self._model_to_entity(model)

    @override
    def update(
        self, entity: BenchmarkRunTestBundleEntity
    ) -> BenchmarkRunTestBundleEntity:
        """Update an existing run test bundle. Entity must have id set."""
        if entity.id is None or entity.id == 0:
            raise ValueError("Cannot update: entity must have id set")
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunTestBundleModel)
                .filter(BenchmarkRunTestBundleModel.id == entity.id)
                .first()
            )
            if model is None:
                raise ValueError(
                    f"Cannot update: no benchmark_run_test_bundle with id={entity.id}"
                )
            model.run_id = entity.run_id
            model.test_bundle_id = entity.test_bundle_id
            model.test_id = entity.test_id
            session.flush()
            return self._model_to_entity(model)
