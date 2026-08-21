"""
Service for listing benchmark run test prompts by benchmark_run id.

Uses existing repository adapters per call so it is safe to use from
async code or different threads.
"""

from typing import Optional

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

    def patch_user_feedback(
        self,
        prompt_row_id: int,
        user_evaluation: Optional[int],
        user_notes: Optional[str],
    ) -> Optional[BenchmarkRunTestPromptEntity]:
        """
        Update user_evaluation and user_notes for a prompt row by primary key.

        Args:
            prompt_row_id: benchmark_run_test_prompt.id
            user_evaluation: 1 (agree), 0 (disagree), or None (clear)
            user_notes: Annotation text; None or whitespace-only stored as NULL.

        Returns:
            Updated entity if the prompt exists; None if not found.

        Raises:
            ValueError: If user_evaluation is not None and not 0 or 1.
        """
        if user_evaluation is not None and user_evaluation not in (0, 1):
            raise ValueError("user_evaluation must be 0, 1, or null")

        prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        entity = prompt_repo.get_by_id(prompt_row_id)
        if entity is None:
            return None

        if user_notes is None:
            notes_val = None
        else:
            notes_val = user_notes.strip() or None

        entity.user_evaluation = user_evaluation
        entity.user_notes = notes_val
        return prompt_repo.update(entity)

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
