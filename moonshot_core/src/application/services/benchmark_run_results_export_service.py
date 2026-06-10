"""
Reconstruct GA Schema1 JSON from DB-backed benchmark run results.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import BenchmarkTestModel
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.benchmark_run_prompt_service import BenchmarkRunPromptService
from application.services.benchmark_run_service import BenchmarkRunService
from application.services.database_connector_config_service import (
    DatabaseConnectorConfigService,
)
from application.services.database_custom_app_connector_config_service import (
    DatabaseCustomAppConnectorConfigService,
)
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.services.enums.module_types import ModuleTypes
from domain.services.ga_results_formatter import (
    add_timing_to_metadata,
    benchmark_run_prompt_to_ga_dict,
    categorise_prompt_dicts,
    format_metadata as format_ga_metadata,
    format_run_metadata,
)
from domain.services.loader.module_loader import ModuleLoader


class BenchmarkRunResultsExportError(ValueError):
    """Export cannot proceed (e.g. run incomplete or missing prompt results)."""


class BenchmarkRunResultsExportService:
    """Build GA Schema1 JSON from a completed DB-backed benchmark run."""

    def export_run(self, run_id: int, *, redact_secrets: bool = True) -> Optional[dict]:
        """
        Return GA Schema1 dict for the run, or None if the run does not exist.

        Raises:
            BenchmarkRunResultsExportError: Run exists but is not exportable.
        """
        run_service = BenchmarkRunService()
        run_entity = run_service.get_run_by_id(run_id)
        if run_entity is None:
            return None

        self._validate_run_exportable(run_entity)

        status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        statuses = status_repo.get_all_by_run_id(run_id)
        if not statuses:
            raise BenchmarkRunResultsExportError(
                f"Benchmark run {run_id} has no test statuses to export."
            )

        prompt_service = BenchmarkRunPromptService()
        all_prompts = prompt_service.get_all_prompts_by_run_id(run_id)
        prompts_by_run_test: dict[int, list] = defaultdict(list)
        for prompt in all_prompts:
            prompts_by_run_test[prompt.run_test_id].append(prompt)

        run_start, run_end = self._run_time_bounds(run_entity, statuses)
        run_metadata = format_run_metadata(run_entity.name, run_start, run_end)

        base_connector = self._build_base_connector(run_entity)
        config_adapter = BenchmarkTestConfigAdapter()

        run_results: list[dict] = []
        for status in sorted(statuses, key=lambda s: s.id or 0):
            if status.id is None:
                continue
            entry = self._build_run_result_entry(
                status=status,
                prompts=prompts_by_run_test.get(status.id, []),
                base_connector=base_connector,
                config_adapter=config_adapter,
                redact_secrets=redact_secrets,
            )
            run_results.append(entry)

        run_results.sort(key=lambda item: item["metadata"]["test_name"])
        return {"run_metadata": run_metadata, "run_results": run_results}

    def export_run_json(
        self, run_id: int, *, indent: int = 4, redact_secrets: bool = True
    ) -> Optional[str]:
        """Return GA Schema1 JSON string, or None if the run does not exist."""
        payload = self.export_run(run_id, redact_secrets=redact_secrets)
        if payload is None:
            return None
        return json.dumps(payload, indent=indent)

    @staticmethod
    def _validate_run_exportable(run_entity: BenchmarkRunEntity) -> None:
        if run_entity.status != "completed":
            raise BenchmarkRunResultsExportError(
                f"Benchmark run {run_entity.name!r} is not completed "
                f"(status={run_entity.status!r})."
            )
        if run_entity.start_time is None or run_entity.end_time is None:
            raise BenchmarkRunResultsExportError(
                f"Benchmark run {run_entity.name!r} is missing start or end time."
            )

    @staticmethod
    def _run_time_bounds(
        run_entity: BenchmarkRunEntity,
        statuses: list[BenchmarkRunTestStatusEntity],
    ) -> tuple[datetime, datetime]:
        start = run_entity.start_time
        end = run_entity.end_time
        assert start is not None and end is not None

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return start, end

    @staticmethod
    def _build_base_connector(run_entity: BenchmarkRunEntity) -> ConnectorEntity:
        if run_entity.endpoint_type == "Custom_App":
            if run_entity.custom_app_id is None or run_entity.custom_app_config_id is None:
                raise BenchmarkRunResultsExportError(
                    f"Benchmark run {run_entity.name!r} is missing custom app connector ids."
                )
            return DatabaseCustomAppConnectorConfigService().build_connector_entity(
                custom_app_id=run_entity.custom_app_id,
                custom_app_config_id=run_entity.custom_app_config_id,
            )

        if (
            run_entity.llm_provider_id is None
            or run_entity.llm_provider_model_id is None
            or run_entity.llm_provider_model_config_id is None
        ):
            raise BenchmarkRunResultsExportError(
                f"Benchmark run {run_entity.name!r} is missing LLM provider connector ids."
            )
        return DatabaseConnectorConfigService().build_connector_entity(
            llm_provider_id=run_entity.llm_provider_id,
            llm_provider_model_id=run_entity.llm_provider_model_id,
            llm_provider_model_config_id=run_entity.llm_provider_model_config_id,
        )

    @staticmethod
    def _apply_status_connector_overrides(
        connector: ConnectorEntity,
        status: BenchmarkRunTestStatusEntity,
    ) -> ConnectorEntity:
        updated = connector.model_copy(deep=True)
        if status.connector_pre_prompt is not None:
            updated.connector_pre_prompt = status.connector_pre_prompt
        if status.connector_post_prompt is not None:
            updated.connector_post_prompt = status.connector_post_prompt
        if status.system_prompt is not None:
            updated.system_prompt = status.system_prompt
        return updated

    @staticmethod
    def _get_test_type(test_id: int) -> str:
        with SessionManager.get_instance().get_session() as session:
            row = (
                session.query(BenchmarkTestModel)
                .filter(BenchmarkTestModel.id == test_id)
                .first()
            )
            if row is None:
                raise BenchmarkRunResultsExportError(
                    f"Benchmark test not found: test_id={test_id}"
                )
            return str(row.type)

    def _build_run_result_entry(
        self,
        *,
        status: BenchmarkRunTestStatusEntity,
        prompts: list,
        base_connector: ConnectorEntity,
        config_adapter: BenchmarkTestConfigAdapter,
        redact_secrets: bool,
    ) -> dict:
        if not prompts:
            raise BenchmarkRunResultsExportError(
                f"Run test status id={status.id} has no prompt results to export."
            )
        if any(p.prediction_result is None for p in prompts):
            raise BenchmarkRunResultsExportError(
                f"Run test status id={status.id} has prompts without predictions."
            )

        test_name, dataset_system_name, metric_name = config_adapter.get_test_info(
            status.test_id
        )
        task_type = self._get_test_type(status.test_id)
        connector = self._apply_status_connector_overrides(base_connector, status)

        prompt_dicts = [benchmark_run_prompt_to_ga_dict(p) for p in prompts]
        prompt_dicts.sort(key=lambda item: item["prompt_id"])
        individual_results = categorise_prompt_dicts(prompt_dicts, metric_name)

        metric_entities = self._to_metric_entities(prompt_dicts)
        evaluation_summary = self._await_coroutine(
            self._compute_evaluation_summary(metric_name, metric_entities)
        )

        metadata = format_ga_metadata(
            test_name,
            dataset_system_name,
            {"name": metric_name},
            connector,
            task_type,
            redact_secrets=redact_secrets,
        )
        add_timing_to_metadata(metadata, status.start_dt, status.end_dt)

        return {
            "metadata": metadata,
            "results": {
                "individual_results": individual_results,
                "evaluation_summary": evaluation_summary,
            },
        }

    @staticmethod
    def _to_metric_entities(prompt_dicts: list[dict]) -> list[MetricIndividualEntity]:
        entities: list[MetricIndividualEntity] = []
        for prompt_dict in prompt_dicts:
            evaluated = prompt_dict.get("evaluated_result") or {}
            if not isinstance(evaluated, dict):
                evaluated = {}
            predicted = prompt_dict.get("predicted_result") or {}
            response = predicted.get("response", "") if isinstance(predicted, dict) else ""
            entities.append(
                MetricIndividualEntity(
                    prompt=prompt_dict.get("prompt", ""),
                    predicted_result=ConnectorResponseEntity(
                        response=response,
                        context=predicted.get("context", []) if isinstance(predicted, dict) else [],
                    ),
                    target=prompt_dict.get("target", ""),
                    evaluated_result=evaluated,
                )
            )
        return entities

    @staticmethod
    def _await_coroutine(coro):
        """Run *coro* to completion from sync code (with or without a running loop)."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()

    @staticmethod
    async def _compute_evaluation_summary(
        metric_name: str, entities: list[MetricIndividualEntity]
    ) -> dict:
        adapter_instance, _ = ModuleLoader.load(metric_name, ModuleTypes.METRIC)
        return await adapter_instance.get_results(entities)
