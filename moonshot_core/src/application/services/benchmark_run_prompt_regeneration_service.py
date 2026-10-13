"""
Regenerate benchmark_run_test_prompt rows: SUT response + metric (LLMAAJ) judgement.

Reuses AsyncioPromptProcessor.process_prompts with write_to_db so existing rows
are updated in place (same path as a normal test run).

Single-prompt regenerate: parent test/run status refresh is handled by
BenchmarkRunStatusRefreshService (called from the API after regenerate).

Bulk regenerate: marks target prompts running (does not flip the parent run to
running), processes error and unknown-evaluation prompts grouped by run_test_id,
refreshes statuses once at the end, and exposes progress via a process-local
job registry.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import (
    SqlAlchemyBenchmarkRunTestPromptRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from adapters.prompt_processor.asyncio_prompt_processor_adapter import (
    AsyncioPromptProcessor,
)
from application.dto.run_bundle_dto import (
    BenchmarkRunTestPromptResponseDTO,
    parse_evaluation_prediction_result,
)
from application.services.benchmark_run_prompt_service import BenchmarkRunPromptService
from application.services.benchmark_run_results_query_service import (
    BenchmarkRunResultsQueryService,
)
from application.services.benchmark_run_service import BenchmarkRunService
from application.services.benchmark_run_status_refresh_service import (
    BenchmarkRunStatusRefreshService,
)
from application.services.database_connector_config_service import (
    DatabaseConnectorConfigService,
)
from application.services.database_custom_app_connector_config_service import (
    DatabaseCustomAppConnectorConfigService,
)
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)
from domain.entities.prompt_entity import PromptEntity
from domain.ports.metric_port import MetricPort
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

_ACTIVE_RUN_STATUSES = frozenset({"running"})
_ACTIVE_TEST_STATUSES = frozenset({"in_progress", "not_started"})
_ACTIVE_PROMPT_STATUSES = frozenset({"running", "pending"})
# While regenerating, persist score 0 so API/UI do not show a stale pass score.
_RUNNING_EVALUATION_RESULT = str({"score": 0})

BulkJobStatus = Literal["in_progress", "completed", "failed"]
ProgressStatus = Literal["idle", "in_progress", "completed", "failed"]


class BenchmarkRunPromptNotFoundError(LookupError):
    """Raised when benchmark_run_test_prompt.id does not exist."""


class BenchmarkRunPromptRegenerationConflictError(RuntimeError):
    """Raised when regenerate would race an in-flight run/test/prompt."""


@dataclass(frozen=True)
class BulkRegenerateStartResult:
    """Snapshot returned after preparing a bulk regenerate job."""

    run_id: int
    total: int
    prompt_ids: list[int]
    run_test_ids: list[int]


@dataclass
class BulkRegenerateJobState:
    """Process-local state for one bulk regenerate job (not multi-worker safe)."""

    prompt_ids: list[int]
    total: int
    status: BulkJobStatus = "in_progress"


@dataclass(frozen=True)
class BulkRegenerateProgress:
    """Progress snapshot for the bulk regenerate progress API."""

    run_id: int
    status: ProgressStatus
    total: int
    done: int
    failed: int


# Process-local registry: fine for single-process BackgroundTasks; shared store
# would be needed for multi-worker deployments.
_bulk_regen_jobs: dict[int, BulkRegenerateJobState] = {}


class BenchmarkRunPromptRegenerationService:
    """Regenerate response + evaluation for one prompt or all failed prompts in a run."""

    async def regenerate(self, prompt_row_id: int) -> BenchmarkRunTestPromptResponseDTO:
        """
        Re-run connector + metric for one prompt and return the enriched DTO.

        Does not refresh parent test/run status; callers should invoke
        BenchmarkRunStatusRefreshService.refresh_after_prompt_update with the
        returned DTO's ``run_test_id``.

        Raises:
            BenchmarkRunPromptNotFoundError: prompt id missing.
            BenchmarkRunPromptRegenerationConflictError: run/test still active.
            DatabaseConnectorConfigError / DatabaseCustomAppConnectorConfigError:
                connector resolution failed.
            ValueError: missing metric or connector configuration on the run.
        """
        prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()

        entity = prompt_repo.get_by_id(prompt_row_id)
        if entity is None:
            raise BenchmarkRunPromptNotFoundError(
                f"Benchmark run test prompt not found: prompt_id={prompt_row_id}"
            )

        status_entity = status_repo.get_by_id(entity.run_test_id)
        if status_entity is None:
            raise BenchmarkRunPromptNotFoundError(
                f"Run test status missing for prompt_id={prompt_row_id}"
            )

        run = BenchmarkRunService().get_run_by_id(status_entity.run_id)
        if run is None:
            raise BenchmarkRunPromptNotFoundError(
                f"Benchmark run not found for prompt_id={prompt_row_id}"
            )

        self._assert_not_conflicting(run, status_entity, entity, prompt_repo)

        _, _, metric_name = BenchmarkTestConfigAdapter().get_test_info(
            status_entity.test_id
        )
        if not metric_name:
            raise ValueError(
                f"No metric configured for test_id={status_entity.test_id}"
            )

        connector_entity = self._build_connector_entity(run)

        entity.status = "running"
        entity.prediction_result = None
        entity.evaluation_prediction_result = _RUNNING_EVALUATION_RESULT
        entity.evaluation_accuracy = 0.0
        prompt_repo.update(entity)

        prompt_entity = PromptEntity(
            index=1,
            prompt=entity.prompt_additional_info or "",
            target=entity.target or "",
            reference_context="",
            model_prediction=None,
            evaluation_result={},
            additional_info={},
            benchmark_run_test_prompt_id=entity.id,
        )

        logger.info(
            "[BenchmarkRunPromptRegenerationService] Regenerating prompt_id=%s "
            "run_test_id=%s metric=%s",
            prompt_row_id,
            entity.run_test_id,
            metric_name,
        )

        processor = AsyncioPromptProcessor()
        await processor.process_prompts(
            [prompt_entity],
            connector_entity,
            {"name": metric_name},
            callback_fn=None,
            write_to_db=True,
            run_test_id=entity.run_test_id,
        )

        updated = prompt_repo.get_by_id(prompt_row_id)
        if updated is None:
            raise BenchmarkRunPromptNotFoundError(
                f"Prompt disappeared after regenerate: prompt_id={prompt_row_id}"
            )

        return BenchmarkRunResultsQueryService().prompt_dto_for_entity(
            status_entity.run_id, updated
        )

    def prepare_regenerate_failed_for_run(
        self, run_id: int
    ) -> BulkRegenerateStartResult:
        """
        Validate and prepare a bulk regenerate job for failed/unknown prompts.

        Targets prompts with ``status=error`` or completed prompts whose
        ``evaluated_response`` is ``unknown``. Marks them ``running`` (and clears
        stale prediction_result / evaluation) but does **not** set the parent run
        to running.
        Registers a process-local job for progress polling. Returns a snapshot of
        prompt ids for the background worker. When there are no targets, leaves
        statuses unchanged and returns ``total=0``.
        """
        existing = _bulk_regen_jobs.get(run_id)
        if existing is not None and existing.status == "in_progress":
            raise BenchmarkRunPromptRegenerationConflictError(
                "Cannot regenerate while a bulk regenerate job is already in progress."
            )

        run_service = BenchmarkRunService()
        run = run_service.get_run_by_id(run_id)
        if run is None:
            raise BenchmarkRunPromptNotFoundError(
                f"Benchmark run not found: run_id={run_id}"
            )

        if (run.status or "").lower() in _ACTIVE_RUN_STATUSES:
            raise BenchmarkRunPromptRegenerationConflictError(
                "Cannot regenerate while the benchmark run is still running."
            )

        prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        all_prompts = BenchmarkRunPromptService().get_all_prompts_by_run_id(run_id)
        targets = [
            p
            for p in all_prompts
            if p.id is not None and self._is_bulk_regenerate_target(p)
        ]
        if not targets:
            return BulkRegenerateStartResult(
                run_id=run_id, total=0, prompt_ids=[], run_test_ids=[]
            )

        target_ids = {p.id for p in targets}
        statuses_by_id: dict[int, BenchmarkRunTestStatusEntity] = {}
        for status_entity in status_repo.get_all_by_run_id(run_id):
            if status_entity.id is not None:
                statuses_by_id[status_entity.id] = status_entity

        self._assert_bulk_not_conflicting(
            targets, statuses_by_id, prompt_repo, target_ids
        )

        for entity in targets:
            entity.status = "running"
            # Clear stale SUT output; pin evaluation score to 0 while regenerating.
            entity.prediction_result = None
            entity.evaluation_prediction_result = _RUNNING_EVALUATION_RESULT
            entity.evaluation_accuracy = 0.0
            prompt_repo.update(entity)

        prompt_ids = [p.id for p in targets if p.id is not None]
        run_test_ids = sorted({p.run_test_id for p in targets})
        _bulk_regen_jobs[run_id] = BulkRegenerateJobState(
            prompt_ids=list(prompt_ids),
            total=len(prompt_ids),
            status="in_progress",
        )
        logger.info(
            "[BenchmarkRunPromptRegenerationService] Prepared bulk regenerate "
            "run_id=%s total=%s run_test_ids=%s",
            run_id,
            len(prompt_ids),
            run_test_ids,
        )
        return BulkRegenerateStartResult(
            run_id=run_id,
            total=len(prompt_ids),
            prompt_ids=prompt_ids,
            run_test_ids=run_test_ids,
        )

    def get_regenerate_failed_progress(self, run_id: int) -> BulkRegenerateProgress:
        """
        Return progress for a bulk regenerate job from the process-local registry.

        ``done`` / ``failed`` are computed by re-reading snapshot prompt rows.
        """
        job = _bulk_regen_jobs.get(run_id)
        if job is None:
            return BulkRegenerateProgress(
                run_id=run_id,
                status="idle",
                total=0,
                done=0,
                failed=0,
            )

        prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        done = 0
        failed = 0
        for prompt_id in job.prompt_ids:
            entity = prompt_repo.get_by_id(prompt_id)
            if entity is None:
                done += 1
                continue
            status = (entity.status or "").lower()
            if status in _ACTIVE_PROMPT_STATUSES:
                continue
            done += 1
            if status == "error":
                failed += 1

        return BulkRegenerateProgress(
            run_id=run_id,
            status=job.status,
            total=job.total,
            done=done,
            failed=failed,
        )

    async def regenerate_failed_for_run(
        self, run_id: int, prompt_ids: list[int]
    ) -> None:
        """
        Process previously prepared failed prompts and refresh parent statuses once.

        Intended to run as a background job after ``prepare_regenerate_failed_for_run``.
        """
        if not prompt_ids:
            self._set_job_status(run_id, "completed")
            return

        prompt_repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        run_service = BenchmarkRunService()

        run = run_service.get_run_by_id(run_id)
        if run is None:
            self._set_job_status(run_id, "failed")
            raise BenchmarkRunPromptNotFoundError(
                f"Benchmark run not found: run_id={run_id}"
            )

        targets: list[BenchmarkRunTestPromptEntity] = []
        for prompt_id in prompt_ids:
            entity = prompt_repo.get_by_id(prompt_id)
            if entity is None:
                logger.warning(
                    "[BenchmarkRunPromptRegenerationService] Skipping missing "
                    "prompt_id=%s during bulk regenerate.",
                    prompt_id,
                )
                continue
            targets.append(entity)

        if not targets:
            BenchmarkRunStatusRefreshService().refresh_after_bulk_prompt_updates(
                run_id, []
            )
            self._set_job_status(run_id, "completed")
            return

        run_test_ids = sorted({p.run_test_id for p in targets})
        job_failed = False
        try:
            connector_entity = self._build_connector_entity(run)
            groups: dict[int, list[BenchmarkRunTestPromptEntity]] = defaultdict(list)
            for entity in targets:
                groups[entity.run_test_id].append(entity)

            processor = AsyncioPromptProcessor()
            for run_test_id, group in groups.items():
                status_entity = status_repo.get_by_id(run_test_id)
                if status_entity is None:
                    logger.error(
                        "[BenchmarkRunPromptRegenerationService] Missing "
                        "run_test_status for run_test_id=%s; marking prompts error.",
                        run_test_id,
                    )
                    for entity in group:
                        entity.status = "error"
                        prompt_repo.update(entity)
                    continue

                _, _, metric_name = BenchmarkTestConfigAdapter().get_test_info(
                    status_entity.test_id
                )
                if not metric_name:
                    logger.error(
                        "[BenchmarkRunPromptRegenerationService] No metric for "
                        "test_id=%s; marking prompts error.",
                        status_entity.test_id,
                    )
                    for entity in group:
                        entity.status = "error"
                        prompt_repo.update(entity)
                    continue

                prompt_entities = [
                    PromptEntity(
                        index=i + 1,
                        prompt=entity.prompt_additional_info or "",
                        target=entity.target or "",
                        reference_context="",
                        model_prediction=None,
                        evaluation_result={},
                        additional_info={},
                        benchmark_run_test_prompt_id=entity.id,
                    )
                    for i, entity in enumerate(group)
                ]

                logger.info(
                    "[BenchmarkRunPromptRegenerationService] Bulk regenerating "
                    "run_id=%s run_test_id=%s count=%s metric=%s",
                    run_id,
                    run_test_id,
                    len(prompt_entities),
                    metric_name,
                )
                await processor.process_prompts(
                    prompt_entities,
                    connector_entity,
                    {"name": metric_name},
                    callback_fn=None,
                    write_to_db=True,
                    run_test_id=run_test_id,
                )
        except Exception:
            job_failed = True
            logger.exception(
                "[BenchmarkRunPromptRegenerationService] Bulk regenerate failed "
                "for run_id=%s; forcing remaining running targets to error.",
                run_id,
            )
            for prompt_id in prompt_ids:
                entity = prompt_repo.get_by_id(prompt_id)
                if entity is not None and (entity.status or "").lower() == "running":
                    entity.status = "error"
                    prompt_repo.update(entity)
            raise
        finally:
            BenchmarkRunStatusRefreshService().refresh_after_bulk_prompt_updates(
                run_id, run_test_ids
            )
            self._set_job_status(run_id, "failed" if job_failed else "completed")

    @staticmethod
    def _set_job_status(run_id: int, status: BulkJobStatus) -> None:
        job = _bulk_regen_jobs.get(run_id)
        if job is not None:
            job.status = status

    @staticmethod
    def clear_bulk_jobs_for_tests() -> None:
        """Reset process-local job registry (tests only)."""
        _bulk_regen_jobs.clear()

    @staticmethod
    def _evaluated_response_is_unknown(raw: str | None) -> bool:
        """True when evaluation blob's evaluated_response is metric unknown."""
        if raw is None:
            return False
        text = str(raw).strip()
        if not text:
            return False
        if text.lower() == MetricPort.RESULT_UNKNOWN.lower():
            return True

        parsed = parse_evaluation_prediction_result(text)
        if isinstance(parsed, dict):
            evaluated = parsed.get("evaluated_response")
            if (
                isinstance(evaluated, str)
                and evaluated.strip().lower() == MetricPort.RESULT_UNKNOWN.lower()
            ):
                return True

        # Fallback for blobs parse_evaluation_prediction_result cannot load.
        match = re.search(
            r"""\bevaluated_response['"]?\s*:\s*['"]([^'"]*)['"]""",
            text,
            flags=re.IGNORECASE,
        )
        if match is None:
            return False
        return match.group(1).strip().lower() == MetricPort.RESULT_UNKNOWN.lower()

    @classmethod
    def _is_bulk_regenerate_target(cls, prompt: BenchmarkRunTestPromptEntity) -> bool:
        """True for status=error or completed prompts with evaluated_response unknown."""
        status = (prompt.status or "").lower()
        if status == "error":
            return True
        if status in _ACTIVE_PROMPT_STATUSES:
            return False
        return cls._evaluated_response_is_unknown(prompt.evaluation_prediction_result)

    @staticmethod
    def _assert_bulk_not_conflicting(
        targets: list[BenchmarkRunTestPromptEntity],
        statuses_by_id: dict[int, BenchmarkRunTestStatusEntity],
        prompt_repo: SqlAlchemyBenchmarkRunTestPromptRepository,
        target_ids: set[int],
    ) -> None:
        for entity in targets:
            status_entity = statuses_by_id.get(entity.run_test_id)
            if status_entity is None:
                raise BenchmarkRunPromptNotFoundError(
                    f"Run test status missing for prompt_id={entity.id}"
                )
            if (status_entity.status or "").lower() in _ACTIVE_TEST_STATUSES:
                raise BenchmarkRunPromptRegenerationConflictError(
                    "Cannot regenerate while the test is still in progress."
                )

        checked_run_tests: set[int] = set()
        for entity in targets:
            if entity.run_test_id in checked_run_tests:
                continue
            checked_run_tests.add(entity.run_test_id)
            siblings = prompt_repo.get_all_by_run_test_id(entity.run_test_id)
            if any(
                p.id not in target_ids and (p.status or "").lower() == "running"
                for p in siblings
            ):
                raise BenchmarkRunPromptRegenerationConflictError(
                    "Cannot regenerate while another prompt in this test is running."
                )

    @staticmethod
    def _assert_not_conflicting(
        run: BenchmarkRunEntity,
        status_entity: BenchmarkRunTestStatusEntity,
        entity: BenchmarkRunTestPromptEntity,
        prompt_repo: SqlAlchemyBenchmarkRunTestPromptRepository,
    ) -> None:
        if (run.status or "").lower() in _ACTIVE_RUN_STATUSES:
            raise BenchmarkRunPromptRegenerationConflictError(
                "Cannot regenerate while the benchmark run is still running."
            )
        if (status_entity.status or "").lower() in _ACTIVE_TEST_STATUSES:
            raise BenchmarkRunPromptRegenerationConflictError(
                "Cannot regenerate while the test is still in progress."
            )
        # Target may already be running (retry / stuck row). Block only when a
        # different sibling prompt in the same test is running.
        siblings = prompt_repo.get_all_by_run_test_id(entity.run_test_id)
        if any(
            p.id != entity.id and (p.status or "").lower() == "running"
            for p in siblings
        ):
            raise BenchmarkRunPromptRegenerationConflictError(
                "Cannot regenerate while another prompt in this test is running."
            )

    @staticmethod
    def _build_connector_entity(run: BenchmarkRunEntity):
        use_llm = (
            run.llm_provider_id is not None
            and run.llm_provider_model_id is not None
            and run.llm_provider_model_config_id is not None
        )
        use_custom_app = (
            run.custom_app_id is not None and run.custom_app_config_id is not None
        )
        if use_llm:
            return DatabaseConnectorConfigService().build_connector_entity(
                llm_provider_id=run.llm_provider_id,
                llm_provider_model_id=run.llm_provider_model_id,
                llm_provider_model_config_id=run.llm_provider_model_config_id,
            )
        if use_custom_app:
            return DatabaseCustomAppConnectorConfigService().build_connector_entity(
                custom_app_id=run.custom_app_id,
                custom_app_config_id=run.custom_app_config_id,
            )
        raise ValueError(
            "Benchmark run has neither LLM provider nor custom app connector ids."
        )
