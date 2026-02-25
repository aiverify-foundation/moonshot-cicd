from abc import ABC, abstractmethod

from domain.entities.benchmark_run_test_prompt_entity import \
    BenchmarkRunTestPromptEntity


class BenchmarkRunTestPromptRepository(ABC):
    """
    Abstract base class for benchmark run test prompt repository implementations.

    This interface defines the contract for accessing per-prompt run results
    (benchmark_run_test_prompt rows) by run_test_id.
    """

    @abstractmethod
    def get_all_by_run_test_id(
        self, run_test_id: int
    ) -> list[BenchmarkRunTestPromptEntity]:
        """
        Return all run prompts for the given run_test_id (benchmark_run_test_status.id).

        Args:
            run_test_id: The benchmark_run_test_status id.

        Returns:
            List of run prompt entities; empty if none exist.
        """
        pass

    @abstractmethod
    def save(
        self, entity: BenchmarkRunTestPromptEntity
    ) -> BenchmarkRunTestPromptEntity:
        """
        Insert a new run prompt. Entity must not have id set.

        Args:
            entity: The run prompt to insert.

        Returns:
            The saved entity with id populated.

        Raises:
            ValueError: If entity already has an id (use update instead).
        """
        pass

    @abstractmethod
    def update(
        self, entity: BenchmarkRunTestPromptEntity
    ) -> BenchmarkRunTestPromptEntity:
        """
        Update an existing run prompt. Entity must have id set.

        Args:
            entity: The run prompt to update.

        Returns:
            The updated entity.

        Raises:
            ValueError: If entity has no id or no row exists with that id.
        """
        pass
