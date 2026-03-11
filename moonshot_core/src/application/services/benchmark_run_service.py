"""
Service for persisting and updating benchmark runs.

Creates a new repository adapter per call so it is safe to use from
async code or different threads.
"""

from typing import Optional

from domain.entities.benchmark_run_entity import BenchmarkRunEntity

from adapters.driven.repository.sqlalchemy.benchmark_run_adapter import (
    SqlAlchemyBenchmarkRunRepository,
)


class BenchmarkRunService:
    """
    Application service for benchmark run create/update.

    Instantiates SqlAlchemyBenchmarkRunRepository per call (cheap)
    so usage is safe from async or multiple threads.
    """

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
