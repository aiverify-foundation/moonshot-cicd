from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.benchmark_run_test_bundle_entity import \
    BenchmarkRunTestBundleEntity


class BenchmarkRunTestBundleRepository(ABC):
    """
    Abstract base class for benchmark run test bundle repository implementations.

    This interface defines the contract for accessing benchmark_run_test_bundle rows.
    """

    @abstractmethod
    def get_by_id(
        self, run_test_bundle_id: int
    ) -> Optional[BenchmarkRunTestBundleEntity]:
        """
        Return the run test bundle row with the given id, or None if not found.

        Args:
            run_test_bundle_id: The benchmark_run_test_bundle id.

        Returns:
            The entity or None.
        """
        pass

    @abstractmethod
    def get_all_by_run_id(self, run_id: int) -> list[BenchmarkRunTestBundleEntity]:
        """
        Return all run test bundles for the given benchmark run id.

        Args:
            run_id: The benchmark_run id.

        Returns:
            List of entities; empty if none exist.
        """
        pass

    @abstractmethod
    def save(
        self, entity: BenchmarkRunTestBundleEntity
    ) -> BenchmarkRunTestBundleEntity:
        """
        Persist a run test bundle. Insert if entity has no id; update if entity has id.

        Args:
            entity: The run test bundle to save.

        Returns:
            The saved entity with id populated.
        """
        pass
