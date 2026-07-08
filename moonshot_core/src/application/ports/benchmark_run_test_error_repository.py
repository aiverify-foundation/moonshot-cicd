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

    @abstractmethod
    def get_latest_by_prompt_ids(
        self, prompt_ids: list[int]
    ) -> dict[int, BenchmarkRunTestErrorEntity]:
        """
        Return the latest error row per prompt id (highest id wins).

        Args:
            prompt_ids: benchmark_run_test_prompt.id values to look up.

        Returns:
            Map of prompt id -> latest error entity; omits prompts with no errors.
        """
        pass
