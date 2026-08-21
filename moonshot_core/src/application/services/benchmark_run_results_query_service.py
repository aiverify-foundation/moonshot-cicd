"""
Assemble benchmark run results (run row, bundle summaries, prompts with test_id) from the DB.
"""

from __future__ import annotations

from typing import Optional

from adapters.driven.repository.sqlalchemy.benchmark_run_test_error_adapter import (
    SqlAlchemyBenchmarkRunTestErrorRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestBundleModel,
    BenchmarkTestBundleModel,
    BenchmarkTestModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.dto.run_bundle_dto import (
    BenchmarkRunResultsBundleSummaryDTO,
    BenchmarkRunResultsResponseDTO,
    BenchmarkRunTestMarginOfErrorDTO,
    BenchmarkRunTestPromptResponseDTO,
    BenchmarkRunTestStatusSummaryDTO,
)
from application.services.benchmark_run_prompt_service import BenchmarkRunPromptService
from application.services.benchmark_run_service import BenchmarkRunService
from application.services.bundle_score_confidence import (
    margin_of_error_by_test,
)
from domain.entities.benchmark_run_test_error_entity import (
    BenchmarkRunTestErrorEntity,
)
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)

# Two-sided tail mass for per-test margin_of_error on GET .../results (95% interval).
RUN_RESULTS_SCORE_CONFIDENCE_ALPHA = 0.05


class BenchmarkRunResultsQueryService:
    """
    Load run header, per-bundle test membership, and all prompts enriched with test_id/test_name.
    """

    def list_prompt_dtos(self, run_id: int) -> list[BenchmarkRunTestPromptResponseDTO]:
        """
        All prompts for the run with test_name and test_id populated from DB.
        """
        prompt_service = BenchmarkRunPromptService()
        entities = prompt_service.get_all_prompts_by_run_id(run_id)
        run_test_to_name, run_test_to_test_id = self._run_test_enrichment_maps(run_id)
        errors_by_prompt_id = self._latest_errors_by_prompt_id(entities)
        return [
            BenchmarkRunTestPromptResponseDTO.model_validate(
                self._prompt_dto_payload(
                    e,
                    run_test_to_name,
                    run_test_to_test_id,
                    errors_by_prompt_id,
                )
            )
            for e in entities
        ]

    def get_results(self, run_id: int) -> Optional[BenchmarkRunResultsResponseDTO]:
        """
        Return full results DTO, or None if the benchmark run does not exist.

        ``test_margin_of_error`` lists ``(test_id, margin_of_error)`` for each ``benchmark_test``
        that appears on at least one prompt in the run: t-interval on the mean of per-prompt
        ``score`` for prompts of that test only, with fixed alpha ``RUN_RESULTS_SCORE_CONFIDENCE_ALPHA``.
        Tests with two or fewer scored prompts always get margin ``0.0``.
        """
        run_service = BenchmarkRunService()
        run_entity = run_service.get_run_by_id(run_id)
        if run_entity is None:
            return None

        bundle_rows = self._load_bundle_summaries(run_id)
        prompts = self.list_prompt_dtos(run_id)
        test_margins = [
            BenchmarkRunTestMarginOfErrorDTO(test_id=tid, margin_of_error=moe)
            for tid, moe in margin_of_error_by_test(
                prompts, RUN_RESULTS_SCORE_CONFIDENCE_ALPHA
            )
        ]
        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        statuses = status_repo.get_all_by_run_id(run_id)
        test_run_status = [
            BenchmarkRunTestStatusSummaryDTO(
                test_id=s.test_id,
                start_dt=s.start_dt,
                end_dt=s.end_dt,
                status=s.status,
            )
            for s in statuses
        ]

        return BenchmarkRunResultsResponseDTO(
            run=run_service.to_response_dto(run_entity),
            bundles=bundle_rows,
            prompts=prompts,
            test_margin_of_error=test_margins,
            test_run_status=test_run_status,
        )

    def _run_test_enrichment_maps(
        self, run_id: int
    ) -> tuple[dict[int, str], dict[int, int]]:
        """run_test_status.id -> (benchmark_test.name, benchmark_test.id)."""
        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        statuses = status_repo.get_all_by_run_id(run_id)
        test_ids = {s.test_id for s in statuses if s.id is not None}
        id_to_name: dict[int, str] = {}
        if test_ids:
            with SessionManager.get_instance().get_session() as session:
                models = (
                    session.query(BenchmarkTestModel)
                    .filter(BenchmarkTestModel.id.in_(test_ids))
                    .all()
                )
                id_to_name = {m.id: m.name for m in models if m.id is not None}

        run_test_to_name: dict[int, str] = {}
        run_test_to_test_id: dict[int, int] = {}
        for st in statuses:
            if st.id is None:
                continue
            run_test_to_test_id[st.id] = st.test_id
            run_test_to_name[st.id] = id_to_name.get(st.test_id, "")
        return run_test_to_name, run_test_to_test_id

    def prompt_dto_for_entity(
        self, run_id: int, entity: BenchmarkRunTestPromptEntity
    ) -> BenchmarkRunTestPromptResponseDTO:
        """Build a response DTO for one prompt row with test_name and test_id enrichment."""
        run_test_to_name, run_test_to_test_id = self._run_test_enrichment_maps(run_id)
        errors_by_prompt_id = self._latest_errors_by_prompt_id([entity])
        return BenchmarkRunTestPromptResponseDTO.model_validate(
            self._prompt_dto_payload(
                entity,
                run_test_to_name,
                run_test_to_test_id,
                errors_by_prompt_id,
            )
        )

    @staticmethod
    def _latest_errors_by_prompt_id(
        entities: list[BenchmarkRunTestPromptEntity],
    ) -> dict[int, BenchmarkRunTestErrorEntity]:
        prompt_ids = [e.id for e in entities if e.id is not None]
        if not prompt_ids:
            return {}
        error_repo = SqlAlchemyBenchmarkRunTestErrorRepository()
        return error_repo.get_latest_by_prompt_ids(prompt_ids)

    @staticmethod
    def _prompt_dto_payload(
        entity: BenchmarkRunTestPromptEntity,
        run_test_to_name: dict[int, str],
        run_test_to_test_id: dict[int, int],
        errors_by_prompt_id: dict[int, BenchmarkRunTestErrorEntity],
    ) -> dict:
        payload = {
            **entity.model_dump(),
            "test_name": run_test_to_name.get(entity.run_test_id, ""),
            "test_id": run_test_to_test_id.get(entity.run_test_id),
        }
        if entity.id is not None:
            error = errors_by_prompt_id.get(entity.id)
            if error is not None:
                payload["error_message"] = error.error_message
                payload["error_source"] = error.error_source
        return payload

    def _load_bundle_summaries(
        self, run_id: int
    ) -> list[BenchmarkRunResultsBundleSummaryDTO]:
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
            # Copy scalars before session closes (avoid detached instance access).
            row_tuples: list[tuple[int, int, str, str]] = [
                (rtb.test_bundle_id, rtb.test_id, bundle.name, bundle.system_name)
                for rtb, bundle in rows
            ]

        by_bundle: dict[int, dict] = {}
        for test_bundle_id, test_id, name, system_name in row_tuples:
            bid = test_bundle_id
            if bid not in by_bundle:
                by_bundle[bid] = {
                    "name": name,
                    "system_name": system_name,
                    "test_ids": set(),
                }
            by_bundle[bid]["test_ids"].add(test_id)

        summaries: list[BenchmarkRunResultsBundleSummaryDTO] = []
        for test_bundle_id in sorted(by_bundle.keys()):
            meta = by_bundle[test_bundle_id]
            summaries.append(
                BenchmarkRunResultsBundleSummaryDTO(
                    test_bundle_id=test_bundle_id,
                    name=meta["name"],
                    system_name=meta["system_name"],
                    test_ids=sorted(meta["test_ids"]),
                )
            )
        return summaries
