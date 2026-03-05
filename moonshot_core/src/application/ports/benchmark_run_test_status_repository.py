from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.benchmark_run_test_status_entity import \
    BenchmarkRunTestStatusEntity


class BenchmarkRunTestStatusRepository(ABC):
    """
    Abstract base class for benchmark run test status repository implementations.

    This interface defines the contract for accessing benchmark_run_test_status rows.
    """

    @abstractmethod
    def get_by_id(
        self, run_test_status_id: int
    ) -> Optional[BenchmarkRunTestStatusEntity]:
        """
        Return the run test status with the given id, or None if not found.

        Args:
            run_test_status_id: The benchmark_run_test_status id.

        Returns:
            The entity or None.
        """
        pass

    @abstractmethod
    def get_all_by_run_id(self, run_id: int) -> list[BenchmarkRunTestStatusEntity]:
        """
        Return all run test statuses for the given benchmark run id.

        Args:
            run_id: The benchmark_run id.

        Returns:
            List of entities; empty if none exist.
        """
        pass

    @abstractmethod
    def get_by_run_and_test(
        self, run_id: int, test_id: int
    ) -> Optional[BenchmarkRunTestStatusEntity]:
        """
        Return the run test status for (run_id, test_id), or None if not found.

        Args:
            run_id: The benchmark_run id.
            test_id: The benchmark_test id.

        Returns:
            The entity or None.
        """
        pass

    @abstractmethod
    def save(
        self, entity: BenchmarkRunTestStatusEntity
    ) -> BenchmarkRunTestStatusEntity:
        """
        Insert a new run test status. Entity must not have id set.

        Args:
            entity: The run test status to insert.

        Returns:
            The saved entity with id populated.

        Raises:
            ValueError: If entity already has an id (use update instead).
        """
        pass

    @abstractmethod
    def update(
        self, entity: BenchmarkRunTestStatusEntity
    ) -> BenchmarkRunTestStatusEntity:
        """
        Update an existing run test status. Entity must have id set.

        Args:
            entity: The run test status to update.

        Returns:
            The updated entity.

        Raises:
            ValueError: If entity has no id or no row exists with that id.
        """
        pass
