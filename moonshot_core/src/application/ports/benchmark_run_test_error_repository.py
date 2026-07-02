from abc import ABC, abstractmethod

from domain.entities.benchmark_run_test_error_entity import (
    BenchmarkRunTestErrorEntity,
)


class BenchmarkRunTestErrorRepository(ABC):
    """
    Abstract repository for benchmark_run_test_error rows.
    """

    @abstractmethod
    def save(self, entity: BenchmarkRunTestErrorEntity) -> BenchmarkRunTestErrorEntity:
        """
        Insert a new error record. Entity must not have id set.

        Returns:
            Saved entity with id populated.
        """
        pass
