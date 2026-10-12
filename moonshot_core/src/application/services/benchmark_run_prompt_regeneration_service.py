"""
Regenerate a single benchmark_run_test_prompt: SUT response + metric (LLMAAJ) judgement.

Reuses AsyncioPromptProcessor.process_prompts with write_to_db so the existing row
is updated in place (same path as a normal test run for one prompt).

Parent test/run status refresh is handled separately by
BenchmarkRunStatusRefreshService (called from the API after regenerate).
"""

from __future__ import annotations

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
from application.dto.run_bundle_dto import BenchmarkRunTestPromptResponseDTO
from application.services.benchmark_run_results_query_service import (
    BenchmarkRunResultsQueryService,
)
from application.services.benchmark_run_service import BenchmarkRunService
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
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

_ACTIVE_RUN_STATUSES = frozenset({"running"})
_ACTIVE_TEST_STATUSES = frozenset({"in_progress", "not_started"})
_ACTIVE_PROMPT_STATUSES = frozenset({"running", "pending"})


class BenchmarkRunPromptNotFoundError(LookupError):
    """Raised when benchmark_run_test_prompt.id does not exist."""


class BenchmarkRunPromptRegenerationConflictError(RuntimeError):
    """Raised when regenerate would race an in-flight run/test/prompt."""


class BenchmarkRunPromptRegenerationService:
    """Regenerate response + evaluation for one prompt row."""

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
        if (entity.status or "").lower() in _ACTIVE_PROMPT_STATUSES:
            raise BenchmarkRunPromptRegenerationConflictError(
                "Cannot regenerate while this prompt is still running."
            )
        siblings = prompt_repo.get_all_by_run_test_id(entity.run_test_id)
        if any((p.status or "").lower() == "running" for p in siblings):
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
