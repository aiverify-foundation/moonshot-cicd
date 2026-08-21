"""
Service for persisting and updating benchmark runs.

Creates a new repository adapter per call so it is safe to use from
async code or different threads.
"""

from typing import Optional

from adapters.driven.repository.sqlalchemy.benchmark_run_adapter import (
    SqlAlchemyBenchmarkRunRepository,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    CustomAppConfigModel,
    LLMProviderModelConfigModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.dto.run_bundle_dto import BenchmarkRunResponseDTO
from domain.entities.benchmark_run_entity import BenchmarkRunEntity


class BenchmarkRunService:
    """
    Application service for benchmark run read/create/update.

    Instantiates SqlAlchemyBenchmarkRunRepository per call (cheap)
    so usage is safe from async or multiple threads.
    """

    def get_all_runs(self) -> list[BenchmarkRunEntity]:
        """
        Return all benchmark runs.

        Returns:
            List of run entities; empty if none exist.
        """
        repo = SqlAlchemyBenchmarkRunRepository()
        return repo.get_all()

    def get_run_by_id(self, run_id: int) -> Optional[BenchmarkRunEntity]:
        """
        Return the benchmark run with the given id, or None if not found.

        Args:
            run_id: The benchmark_run id.

        Returns:
            The run entity or None.
        """
        repo = SqlAlchemyBenchmarkRunRepository()
        return repo.get_by_id(run_id)

    def get_run_by_name(self, name: str) -> Optional[BenchmarkRunEntity]:
        """
        Return the benchmark run with the given name, or None if not found.

        Args:
            name: The unique run name.

        Returns:
            The run entity or None.
        """
        repo = SqlAlchemyBenchmarkRunRepository()
        return repo.get_by_name(name)

    def save_run(self, entity: BenchmarkRunEntity) -> BenchmarkRunEntity:
        """
        Persist a new benchmark run. Returns the entity with id populated.

        Args:
            entity: The run to save (id should be None for insert).

        Returns:
            The saved entity with id set.
        """
        repo = SqlAlchemyBenchmarkRunRepository()
        return repo.save(entity)

    def update_run(self, entity: BenchmarkRunEntity) -> BenchmarkRunEntity:
        """
        Update an existing benchmark run (e.g. end_time, status).
        Entity must have id set.

        Args:
            entity: The run to update.

        Returns:
            The updated entity.
        """
        repo = SqlAlchemyBenchmarkRunRepository()
        return repo.update(entity)

    @staticmethod
    def resolve_endpoint_config_name(entity: BenchmarkRunEntity) -> Optional[str]:
        """
        Return the user-facing configuration name linked to the run, if any.

        LLM runs use llm_provider_model_config.name; custom app runs use
        custom_app_config.name.
        """
        if entity.llm_provider_model_config_id is not None:
            with SessionManager.get_instance().get_session() as session:
                row = (
                    session.query(LLMProviderModelConfigModel)
                    .filter(
                        LLMProviderModelConfigModel.id
                        == entity.llm_provider_model_config_id
                    )
                    .first()
                )
                return row.name if row is not None else None
        if entity.custom_app_config_id is not None:
            with SessionManager.get_instance().get_session() as session:
                row = (
                    session.query(CustomAppConfigModel)
                    .filter(CustomAppConfigModel.id == entity.custom_app_config_id)
                    .first()
                )
                return row.name if row is not None else None
        return None

    def to_response_dto(self, entity: BenchmarkRunEntity) -> BenchmarkRunResponseDTO:
        """Map a run entity to the API response DTO with endpoint_config_name."""
        return BenchmarkRunResponseDTO.model_validate(
            {
                **entity.model_dump(),
                "endpoint_config_name": self.resolve_endpoint_config_name(entity),
            }
        )
