"""
Resume an interrupted benchmark run: mark it running and re-spawn incomplete work.

Used by POST /api/benchmark-runs/{run_id}/resume (feature flag AIVET_OCT2026_MOON796).
"""

from __future__ import annotations

from dataclasses import dataclass

from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import (
    SqlAlchemyBenchmarkRunTestPromptRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestBundleModel,
    BenchmarkTestBundleModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.benchmark_execution_service import BenchmarkExecutionService
from application.services.benchmark_run_service import BenchmarkRunService
from application.services.benchmark_run_test_status_service import (
    BenchmarkRunTestStatusService,
)
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

_NON_TERMINAL_TEST_STATUSES = frozenset({"not_started", "in_progress", "running"})
_INCOMPLETE_PROMPT_STATUSES = frozenset({"pending", "running"})


class BenchmarkRunResumeNotFoundError(LookupError):
    """Raised when benchmark_run.id does not exist."""


class BenchmarkRunResumeConflictError(RuntimeError):
    """Raised when there is nothing incomplete to resume."""


class BenchmarkRunResumeBadRequestError(ValueError):
    """Raised when the run cannot be resumed (e.g. missing connector config)."""


@dataclass(frozen=True)
class ResumeBenchmarkRunResult:
    """Snapshot returned after starting a resume."""

    run_id: int
    message: str
    resumed_test_count: int


class BenchmarkRunResumeService:
    """Mark a run running again and re-launch incomplete bundle workers."""

    def resume(self, run_id: int) -> ResumeBenchmarkRunResult:
        """
        Resume incomplete work for ``run_id``.

        Sets the parent run to ``running``, resets incomplete tests to
        ``not_started`` and stuck ``running`` prompts to ``pending``, then
        spawns background workers for bundles that still have incomplete tests.
        """
        run_service = BenchmarkRunService()
        run_entity = run_service.get_run_by_id(run_id)
        if run_entity is None:
            raise BenchmarkRunResumeNotFoundError(
                f"Benchmark run not found: id={run_id}"
            )

        self._require_connector_config(run_entity)

        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        status_service = BenchmarkRunTestStatusService()

        run_statuses = status_repo.get_all_by_run_id(run_id)
        incomplete_statuses = self._incomplete_statuses(run_statuses, prompt_repo)
        if not incomplete_statuses:
            raise BenchmarkRunResumeConflictError(
                "Nothing to resume: no incomplete tests or prompts for this run."
            )

        run_entity.status = "running"
        run_entity.end_time = None
        run_service.update_run(run_entity)

        for status_entity in incomplete_statuses:
            status_entity.status = "not_started"
            status_entity.end_dt = None
            status_service.update_run_test_status(status_entity)
            if status_entity.id is None:
                continue
            for prompt in prompt_repo.get_all_by_run_test_id(status_entity.id):
                if (prompt.status or "").lower() == "running":
                    prompt.status = "pending"
                    prompt_repo.update(prompt)

        incomplete_test_ids = {s.test_id for s in incomplete_statuses}
        bundles = self._load_bundles_with_incomplete_tests(run_id, incomplete_test_ids)
        if not bundles:
            raise BenchmarkRunResumeConflictError(
                "Nothing to resume: incomplete tests are not linked to any bundle."
            )

        execution_service = BenchmarkExecutionService()
        for system_name, test_ids in bundles.items():
            execution_service.start_bundle_in_background(
                system_name,
                run_id,
                llm_provider_id=run_entity.llm_provider_id,
                llm_provider_model_id=run_entity.llm_provider_model_id,
                llm_provider_model_config_id=run_entity.llm_provider_model_config_id,
                custom_app_id=run_entity.custom_app_id,
                custom_app_config_id=run_entity.custom_app_config_id,
                test_ids=sorted(test_ids),
                continue_on_test_failure=True,
            )
            logger.info(
                "[BenchmarkRunResumeService] Resumed bundle %s for run_id=%s "
                "test_ids=%s",
                system_name,
                run_id,
                sorted(test_ids),
            )

        resumed_test_count = len(incomplete_test_ids)
        return ResumeBenchmarkRunResult(
            run_id=run_id,
            message="Benchmark run resume started.",
            resumed_test_count=resumed_test_count,
        )

    @staticmethod
    def _require_connector_config(run_entity: BenchmarkRunEntity) -> None:
        use_llm = (
            run_entity.llm_provider_id is not None
            and run_entity.llm_provider_model_id is not None
            and run_entity.llm_provider_model_config_id is not None
        )
        use_custom = (
            run_entity.custom_app_id is not None
            and run_entity.custom_app_config_id is not None
        )
        if not use_llm and not use_custom:
            raise BenchmarkRunResumeBadRequestError(
                "Cannot resume: run is missing LLM provider or custom app connector ids."
            )

    @staticmethod
    def _incomplete_statuses(
        run_statuses: list[BenchmarkRunTestStatusEntity],
        prompt_repo: SqlAlchemyBenchmarkRunTestPromptRepository,
    ) -> list[BenchmarkRunTestStatusEntity]:
        incomplete: list[BenchmarkRunTestStatusEntity] = []
        for status_entity in run_statuses:
            status = (status_entity.status or "").lower()
            if status in _NON_TERMINAL_TEST_STATUSES:
                incomplete.append(status_entity)
                continue
            if status_entity.id is None:
                continue
            prompts = prompt_repo.get_all_by_run_test_id(status_entity.id)
            if any(
                (p.status or "").lower() in _INCOMPLETE_PROMPT_STATUSES for p in prompts
            ):
                incomplete.append(status_entity)
        return incomplete

    @staticmethod
    def _load_bundles_with_incomplete_tests(
        run_id: int, incomplete_test_ids: set[int]
    ) -> dict[str, set[int]]:
        """
        Map bundle system_name -> incomplete test ids for this run.

        Uses the same join pattern as BenchmarkRunResultsQueryService.
        """
        with SessionManager.get_instance().get_session() as session:
            rows = (
                session.query(BenchmarkRunTestBundleModel, BenchmarkTestBundleModel)
                .join(
                    BenchmarkTestBundleModel,
                    BenchmarkRunTestBundleModel.test_bundle_id
                    == BenchmarkTestBundleModel.id,
                )
                .filter(BenchmarkRunTestBundleModel.run_id == run_id)
                .all()
            )
            row_tuples: list[tuple[str, int]] = [
                (bundle.system_name, rtb.test_id) for rtb, bundle in rows
            ]

        by_bundle: dict[str, set[int]] = {}
        for system_name, test_id in row_tuples:
            if test_id not in incomplete_test_ids:
                continue
            by_bundle.setdefault(system_name, set()).add(test_id)
        return by_bundle
