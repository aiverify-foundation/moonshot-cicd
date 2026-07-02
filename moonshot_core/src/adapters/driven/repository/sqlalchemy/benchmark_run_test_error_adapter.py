"""SQLAlchemy-based implementation of BenchmarkRunTestErrorRepository."""

from typing import override

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestErrorModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.benchmark_run_test_error_repository import (
    BenchmarkRunTestErrorRepository,
)
from domain.entities.benchmark_run_test_error_entity import (
    BenchmarkRunTestErrorEntity,
)
from domain.services.logger import get_logger


class SqlAlchemyBenchmarkRunTestErrorRepository(BenchmarkRunTestErrorRepository):
    """Persists benchmark_run_test_error rows via BenchmarkRunTestErrorModel."""

    def __init__(self):
        self.session_manager = SessionManager.get_instance()
        self.logger = get_logger(__name__)

    @staticmethod
    def _model_to_entity(model: BenchmarkRunTestErrorModel) -> BenchmarkRunTestErrorEntity:
        return BenchmarkRunTestErrorEntity(
            id=model.id,
            benchmark_run_test_prompt_id=model.benchmark_run_test_prompt_id,
            error_message=model.error_message,
            error_source=model.error_source,
        )

    @override
    def save(self, entity: BenchmarkRunTestErrorEntity) -> BenchmarkRunTestErrorEntity:
        if entity.id is not None and entity.id != 0:
            raise ValueError(
                "Cannot save: entity has id set. Use update for existing error rows."
            )
        with self.session_manager.get_session() as session:
            model = BenchmarkRunTestErrorModel(
                benchmark_run_test_prompt_id=entity.benchmark_run_test_prompt_id,
                error_message=entity.error_message,
                error_source=entity.error_source,
            )
            session.add(model)
            session.flush()
            return self._model_to_entity(model)
