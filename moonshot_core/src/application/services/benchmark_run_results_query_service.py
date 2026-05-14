"""
Assemble benchmark run results (run row, bundle summaries, prompts with test_id) from the DB.
"""

from __future__ import annotations

from typing import Optional

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
    BenchmarkRunResponseDTO,
    BenchmarkRunResultsBundleSummaryDTO,
    BenchmarkRunResultsResponseDTO,
    BenchmarkRunTestPromptResponseDTO,
)
from application.services.bundle_score_confidence import (
    per_test_mean_scores_for_bundle,
    t_confidence_interval_stats,
)
from application.services.benchmark_run_prompt_service import BenchmarkRunPromptService
from application.services.benchmark_run_service import BenchmarkRunService
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)

# Two-sided tail mass for per-bundle margin_of_error (95% interval).
BUNDLE_SCORE_CONFIDENCE_ALPHA = 0.05


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
        return [
            BenchmarkRunTestPromptResponseDTO.model_validate(
                {
                    **e.model_dump(),
                    "test_name": run_test_to_name.get(e.run_test_id, ""),
                    "test_id": run_test_to_test_id.get(e.run_test_id),
                }
            )
            for e in entities
        ]

    def get_results(self, run_id: int) -> Optional[BenchmarkRunResultsResponseDTO]:
        """
        Return full results DTO, or None if the benchmark run does not exist.

        Each bundle includes ``margin_of_error`` for a t-interval on the mean of per-test
        scores (mean ``evaluation_accuracy`` per test in that bundle only), using a fixed
        two-sided tail mass ``BUNDLE_SCORE_CONFIDENCE_ALPHA`` (0.05, i.e. 95% CI). Bundles
        with two or fewer tests always get ``margin_of_error`` ``0.0``.
        """
        run_service = BenchmarkRunService()
        run_entity = run_service.get_run_by_id(run_id)
        if run_entity is None:
            return None

        bundle_rows = self._load_bundle_summaries(run_id)
        prompts = self.list_prompt_dtos(run_id)
        bundles = [
            self._bundle_with_score_confidence(b, prompts) for b in bundle_rows
        ]

        return BenchmarkRunResultsResponseDTO(
            run=BenchmarkRunResponseDTO.model_validate(run_entity.model_dump()),
            bundles=bundles,
            prompts=prompts,
        )

    def _bundle_with_score_confidence(
        self,
        bundle: BenchmarkRunResultsBundleSummaryDTO,
        prompts: list[BenchmarkRunTestPromptResponseDTO],
    ) -> BenchmarkRunResultsBundleSummaryDTO:
        values = per_test_mean_scores_for_bundle(prompts, bundle.test_ids)
        stats = t_confidence_interval_stats(
            values,
            BUNDLE_SCORE_CONFIDENCE_ALPHA,
            tests_in_bundle=len(bundle.test_ids),
        )
        margin = stats["margin_of_error"]
        if len(bundle.test_ids) <= 2:
            margin = 0.0
        return bundle.model_copy(update={"margin_of_error": margin})

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
        return BenchmarkRunTestPromptResponseDTO.model_validate(
            {
                **entity.model_dump(),
                "test_name": run_test_to_name.get(entity.run_test_id, ""),
                "test_id": run_test_to_test_id.get(entity.run_test_id),
            }
        )

    def _load_bundle_summaries(self, run_id: int) -> list[BenchmarkRunResultsBundleSummaryDTO]:
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
