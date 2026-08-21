from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.benchmark_run_entity import BenchmarkRunEntity


class BenchmarkRunRepository(ABC):
    """
    Abstract base class for benchmark run repository implementations.

    This interface defines the contract for accessing benchmark_run rows.
    """

    @abstractmethod
    def get_by_id(self, run_id: int) -> Optional[BenchmarkRunEntity]:
        """
        Return the benchmark run with the given id, or None if not found.

        Args:
            run_id: The benchmark_run id.

        Returns:
            The run entity or None.
        """
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[BenchmarkRunEntity]:
        """
        Return the benchmark run with the given name, or None if not found.

        Args:
            name: The unique run name.

        Returns:
            The run entity or None.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[BenchmarkRunEntity]:
        """
        Return all benchmark runs.

        Returns:
            List of run entities; empty if none exist.
        """
        pass

    @abstractmethod
    def save(self, entity: BenchmarkRunEntity) -> BenchmarkRunEntity:
        """
        Insert a new benchmark run. Entity must not have id set.

        Args:
            entity: The run to insert.

        Returns:
            The saved entity with id populated.

        Raises:
            ValueError: If entity already has an id (use update instead).
        """
        pass

    @abstractmethod
    def update(self, entity: BenchmarkRunEntity) -> BenchmarkRunEntity:
        """
        Update an existing benchmark run. Entity must have id set.

        Args:
            entity: The run to update (must have id).

        Returns:
            The updated entity.
        """
        pass
