"""SQLAlchemy implementation of BenchmarkRunTestPromptMetricReasoningRepository."""

from typing import override

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestPromptMetricReasoningModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.benchmark_run_test_prompt_metric_reasoning_repository import (
    BenchmarkRunTestPromptMetricReasoningRepository,
)
from domain.entities.benchmark_run_test_prompt_metric_reasoning_entity import (
    BenchmarkRunTestPromptMetricReasoningEntity,
)
from domain.services.logger import get_logger


class SqlAlchemyBenchmarkRunTestPromptMetricReasoningRepository(
    BenchmarkRunTestPromptMetricReasoningRepository
):
    """Persists metric-reasoning rows. Insert only; current row is highest id."""

    def __init__(self):
        self.session_manager = SessionManager.get_instance()
        self.logger = get_logger(__name__)

    @staticmethod
    def _model_to_entity(
        model: BenchmarkRunTestPromptMetricReasoningModel,
    ) -> BenchmarkRunTestPromptMetricReasoningEntity:
        return BenchmarkRunTestPromptMetricReasoningEntity(
            id=model.id,
            benchmark_run_test_prompt_id=model.benchmark_run_test_prompt_id,
            reasoning=model.reasoning,
            create_dt=model.create_dt,
        )

    @staticmethod
    def _require_reasoning(reasoning: object) -> str:
        if not isinstance(reasoning, str) or not reasoning.strip():
            raise ValueError(
                "reasoning must be a non-empty string; no row is stored when "
                "the metric produces no reasoning"
            )
        return reasoning

    @override
    def add_metric_reasoning(
        self, benchmark_run_test_prompt_id: int, reasoning: str
    ) -> BenchmarkRunTestPromptMetricReasoningEntity:
        stored = self._require_reasoning(reasoning)
        with self.session_manager.get_session() as session:
            model = BenchmarkRunTestPromptMetricReasoningModel(
                benchmark_run_test_prompt_id=benchmark_run_test_prompt_id,
                reasoning=stored,
            )
            session.add(model)
            session.flush()
            session.refresh(model)
            return self._model_to_entity(model)

    @override
    def get_latest_metric_reasoning(
        self, benchmark_run_test_prompt_id: int
    ) -> BenchmarkRunTestPromptMetricReasoningEntity | None:
        found = self.get_latest_metric_reasoning_for_prompts(
            [benchmark_run_test_prompt_id]
        )
        return found.get(benchmark_run_test_prompt_id)

    @override
    def get_latest_metric_reasoning_for_prompts(
        self, prompt_ids: list[int]
    ) -> dict[int, BenchmarkRunTestPromptMetricReasoningEntity]:
        if not prompt_ids:
            return {}
        with self.session_manager.get_session() as session:
            models = (
                session.query(BenchmarkRunTestPromptMetricReasoningModel)
                .filter(
                    BenchmarkRunTestPromptMetricReasoningModel.benchmark_run_test_prompt_id.in_(
                        prompt_ids
                    )
                )
                .order_by(BenchmarkRunTestPromptMetricReasoningModel.id.desc())
                .all()
            )
            latest: dict[int, BenchmarkRunTestPromptMetricReasoningEntity] = {}
            for model in models:
                pid = model.benchmark_run_test_prompt_id
                if pid not in latest:
                    latest[pid] = self._model_to_entity(model)
            return latest
