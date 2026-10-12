"""
Refresh parent benchmark_run_test_status and benchmark_run after a prompt change.

Used by the regenerate API after BenchmarkRunPromptRegenerationService updates
a single prompt row.
"""

from __future__ import annotations

from datetime import datetime, timezone

from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import (
    SqlAlchemyBenchmarkRunTestPromptRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
from application.services.benchmark_run_service import BenchmarkRunService
from application.services.benchmark_run_test_status_service import (
    BenchmarkRunTestStatusService,
)
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

_NON_TERMINAL_TEST_STATUSES = frozenset({"in_progress", "not_started", "running"})
_TERMINAL_TEST_STATUSES = frozenset(
    {"completed", "completed_with_errors", "failed", "skipped"}
)


class BenchmarkRunStatusRefreshService:
    """Derive parent test and run statuses from current prompt rows."""

    def refresh_after_prompt_update(self, run_test_id: int) -> None:
        """
        Refresh ``benchmark_run_test_status`` for ``run_test_id`` and the parent
        ``benchmark_run`` from sibling / run-wide prompt statuses.
        """
        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()

        status_entity = status_repo.get_by_id(run_test_id)
        if status_entity is None:
            logger.warning(
                "[BenchmarkRunStatusRefreshService] No run_test_status for "
                "run_test_id=%s; skipping refresh.",
                run_test_id,
            )
            return

        self._refresh_run_test_status(status_entity, prompt_repo)
        self._refresh_run_status(status_entity.run_id, prompt_repo, status_repo)

    @staticmethod
    def _refresh_run_test_status(
        status_entity: BenchmarkRunTestStatusEntity,
        prompt_repo: SqlAlchemyBenchmarkRunTestPromptRepository,
    ) -> None:
        """Update parent test status from sibling prompt statuses."""
        if status_entity.id is None:
            return
        prompts = prompt_repo.get_all_by_run_test_id(status_entity.id)
        if not prompts:
            return
        statuses = {(p.status or "").lower() for p in prompts}
        if "running" in statuses or "pending" in statuses:
            return
        has_errors = "error" in statuses
        if has_errors and statuses <= {"error"}:
            new_status = "failed"
        elif has_errors:
            new_status = "completed_with_errors"
        elif statuses <= {"completed"}:
            new_status = "completed"
        else:
            return

        status_entity.status = new_status
        status_entity.end_dt = datetime.now(timezone.utc)
        BenchmarkRunTestStatusService().update_run_test_status(status_entity)

    @staticmethod
    def _refresh_run_status(
        run_id: int,
        prompt_repo: SqlAlchemyBenchmarkRunTestPromptRepository,
        status_repo: SqlAlchemyBenchmarkRunTestStatusRepository,
    ) -> None:
        """
        Update benchmark_run.status from all tests/prompts.

        Leaves run unchanged while any test is still non-terminal. Otherwise sets
        ``failed`` if any prompt is in error, else ``completed``.
        """
        run_service = BenchmarkRunService()
        run_entity = run_service.get_run_by_id(run_id)
        if run_entity is None:
            return

        run_statuses = status_repo.get_all_by_run_id(run_id)
        if not run_statuses:
            return

        if any(
            (s.status or "").lower() in _NON_TERMINAL_TEST_STATUSES
            for s in run_statuses
        ):
            return

        if not all(
            (s.status or "").lower() in _TERMINAL_TEST_STATUSES for s in run_statuses
        ):
            return

        all_prompts: list[BenchmarkRunTestPromptEntity] = []
        for st in run_statuses:
            if st.id is None:
                continue
            all_prompts.extend(prompt_repo.get_all_by_run_test_id(st.id))

        has_prompt_errors = any(
            (p.status or "").lower() == "error" for p in all_prompts
        )
        new_status = "failed" if has_prompt_errors else "completed"
        if (run_entity.status or "").lower() == new_status:
            return

        run_entity.status = new_status
        run_entity.end_time = datetime.now(timezone.utc)
        run_service.update_run(run_entity)
        logger.info(
            "[BenchmarkRunStatusRefreshService] Benchmark run %s marked as %s "
            "after prompt update.",
            run_id,
            new_status,
        )
