"""
Service for persisting and updating benchmark run test status.

Creates a new repository adapter per call so it is safe to use from
async code or different threads.
"""

from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)

from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)


class BenchmarkRunTestStatusService:
    """
    Application service for benchmark run test status create/update.

    Instantiates SqlAlchemyBenchmarkRunTestStatusRepository per call (cheap)
    so usage is safe from async or multiple threads.
    """

    def save_run_test_status(
        self, entity: BenchmarkRunTestStatusEntity
    ) -> BenchmarkRunTestStatusEntity:
        """
        Insert a new run test status. Entity must not have id set.

        Args:
            entity: The run test status to insert.

        Returns:
            The saved entity with id populated.
        """
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        return repo.save(entity)

    def update_run_test_status(
        self, entity: BenchmarkRunTestStatusEntity
    ) -> BenchmarkRunTestStatusEntity:
        """
        Update an existing run test status. Entity must have id set.

        Args:
            entity: The run test status to update.

        Returns:
            The updated entity.
        """
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        return repo.update(entity)
