"""
Service for listing benchmark_run_test_bundle rows by benchmark_run id.

Uses the repository adapter per call so it is safe to use from
async code or different threads.
"""

from adapters.driven.repository.sqlalchemy.benchmark_run_test_bundle_adapter import (
    SqlAlchemyBenchmarkRunTestBundleRepository,
)
from domain.entities.benchmark_run_test_bundle_entity import (
    BenchmarkRunTestBundleEntity,
)


class BenchmarkRunTestBundleQueryService:
    """
    Application service for listing all run-test-bundle link rows for a benchmark run.
    """

    def get_all_by_run_id(self, run_id: int) -> list[BenchmarkRunTestBundleEntity]:
        """
        Return all benchmark_run_test_bundle entities for the given benchmark_run id.

        Args:
            run_id: The benchmark_run id.

        Returns:
            List of entities; empty if none exist.
        """
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        return repo.get_all_by_run_id(run_id)
