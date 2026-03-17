"""
Service for listing benchmark run test prompts by benchmark_run id.

Uses existing repository adapters per call so it is safe to use from
async code or different threads.
"""

from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import (
    SqlAlchemyBenchmarkRunTestPromptRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)


class BenchmarkRunPromptService:
    """
    Application service for listing all run test prompts for a benchmark run.

    Instantiates repository adapters per call so usage is safe from
    async or multiple threads.
    """

    def get_all_prompts_by_run_id(
        self, run_id: int
    ) -> list[BenchmarkRunTestPromptEntity]:
        """
        Return all benchmark_run_test_prompt entities for the given benchmark_run id.

        Fetches all run-test statuses for the run, then all prompts for each
        run-test, and returns a single flattened list.

        Args:
            run_id: The benchmark_run id.

        Returns:
            List of run test prompt entities; empty if the run has no statuses
            or prompts.
        """
        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        statuses = status_repo.get_all_by_run_id(run_id)
        result: list[BenchmarkRunTestPromptEntity] = []
        for status in statuses:
            prompts = prompt_repo.get_all_by_run_test_id(status.id)
            result.extend(prompts)
        return result
