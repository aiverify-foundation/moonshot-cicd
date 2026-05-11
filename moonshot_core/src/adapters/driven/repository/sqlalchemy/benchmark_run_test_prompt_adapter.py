"""SQLAlchemy-based implementation of BenchmarkRunTestPromptRepository."""

from typing import Optional, override

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestPromptModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import \
    SessionManager
from application.ports.benchmark_run_test_prompt_repository import \
    BenchmarkRunTestPromptRepository
from domain.entities.benchmark_run_test_prompt_entity import \
    BenchmarkRunTestPromptEntity
from domain.services.logger import configure_logger


class SqlAlchemyBenchmarkRunTestPromptRepository(BenchmarkRunTestPromptRepository):
    """
    SQLAlchemy-based implementation of BenchmarkRunTestPromptRepository.

    Reads benchmark_run_test_prompt rows via BenchmarkRunTestPromptModel.
    Uses SessionManager for DB access.
    """

    def __init__(self):
        self.session_manager = SessionManager.get_instance()
        self.logger = configure_logger(__name__)

    def _model_to_entity(
        self, model: BenchmarkRunTestPromptModel
    ) -> BenchmarkRunTestPromptEntity:
        """Map BenchmarkRunTestPromptModel to BenchmarkRunTestPromptEntity."""
        return BenchmarkRunTestPromptEntity(
            id=model.id,
            run_test_id=model.run_test_id,
            prompt_id=model.prompt_id,
            status=model.status,
            target=model.target or "",
            prompt_additional_info=model.prompt_additional_info,
            prediction_result=model.prediction_result,
            prediction_context=model.prediction_context,
            evaluation_prompt=model.evaluation_prompt,
            evaluation_prediction_result=model.evaluation_prediction_result,
            evaluation_accuracy=model.evaluation_accuracy,
            user_evaluation=model.user_evaluation,
            user_notes=model.user_notes,
        )

    @override
    def get_all_by_run_test_id(
        self, run_test_id: int
    ) -> list[BenchmarkRunTestPromptEntity]:
        """
        Return all run prompts for the given run_test_id.

        Args:
            run_test_id: The benchmark_run_test_status id.

        Returns:
            List of run prompt entities; empty if none exist.
        """
        with self.session_manager.get_session() as session:
            models = (
                session.query(BenchmarkRunTestPromptModel)
                .filter(BenchmarkRunTestPromptModel.run_test_id == run_test_id)
                .all()
            )
            return [self._model_to_entity(m) for m in models]

    @override
    def get_by_id(
        self, prompt_row_id: int
    ) -> Optional[BenchmarkRunTestPromptEntity]:
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunTestPromptModel)
                .filter(BenchmarkRunTestPromptModel.id == prompt_row_id)
                .first()
            )
            if model is None:
                return None
            return self._model_to_entity(model)

    @override
    def save(
        self, entity: BenchmarkRunTestPromptEntity
    ) -> BenchmarkRunTestPromptEntity:
        """
        Insert a run prompt. Entity must not have id set.
        Returns the saved entity with id populated.
        """
        if entity.id is not None and entity.id != 0:
            raise ValueError(
                "Cannot save: entity has id set. Use update() for existing run prompt."
            )
        with self.session_manager.get_session() as session:
            model = BenchmarkRunTestPromptModel(
                run_test_id=entity.run_test_id,
                prompt_id=entity.prompt_id,
                status=entity.status,
                target=entity.target,
                prompt_additional_info=entity.prompt_additional_info,
                prediction_result=entity.prediction_result,
                prediction_context=entity.prediction_context,
                evaluation_prompt=entity.evaluation_prompt,
                evaluation_prediction_result=entity.evaluation_prediction_result,
                evaluation_accuracy=entity.evaluation_accuracy,
                user_evaluation=entity.user_evaluation,
                user_notes=entity.user_notes,
            )
            session.add(model)
            session.flush()
            return self._model_to_entity(model)

    @override
    def update(
        self, entity: BenchmarkRunTestPromptEntity
    ) -> BenchmarkRunTestPromptEntity:
        """Update an existing run prompt. Entity must have id set."""
        if entity.id is None or entity.id == 0:
            raise ValueError("Cannot update: entity must have id set")
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkRunTestPromptModel)
                .filter(BenchmarkRunTestPromptModel.id == entity.id)
                .first()
            )
            if model is None:
                raise ValueError(
                    f"Cannot update: no benchmark_run_test_prompt with id={entity.id}"
                )
            model.run_test_id = entity.run_test_id
            model.prompt_id = entity.prompt_id
            model.status = entity.status
            model.target = entity.target
            model.prompt_additional_info = entity.prompt_additional_info
            model.prediction_result = entity.prediction_result
            model.prediction_context = entity.prediction_context
            model.evaluation_prompt = entity.evaluation_prompt
            model.evaluation_prediction_result = entity.evaluation_prediction_result
            model.evaluation_accuracy = entity.evaluation_accuracy
            model.user_evaluation = entity.user_evaluation
            model.user_notes = entity.user_notes
            session.flush()
            return self._model_to_entity(model)
