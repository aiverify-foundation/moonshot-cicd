#!/usr/bin/env python3
"""
Inject a running (in-progress) benchmark run from a JSON fixture into the E2E/test database.

Loads system_test/fixtures/e2e_run_progress_monitor.json and inserts related rows with FK
remapping. Writes .e2e-progress-run.json for Playwright progress-monitor tests.

Usage:
  MOONSHOT_DB_PATH=... PYTHONPATH=moonshot_core python system_test/scripts/seed_running_progress_run.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MOONSHOT_CORE_ROOT = REPO_ROOT / "moonshot_core"
SRC_PATH = MOONSHOT_CORE_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from adapters.driven.repository.sqlalchemy.llm_provider_models import (  # noqa: E402
    BenchmarkRunModel,
    BenchmarkRunTestBundleModel,
    BenchmarkRunTestPromptModel,
    BenchmarkRunTestStatusModel,
    BenchmarkTestBundleGroupingModel,
    BenchmarkTestBundleModel,
    BenchmarkTestDatasetModel,
    BenchmarkTestDatasetPromptModel,
    BenchmarkTestMetricModel,
    BenchmarkTestModel,
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelConfigParametersModel,
    LLMProviderModelModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager  # noqa: E402
from application.services.benchmark_run_prompt_service import (  # noqa: E402
    BenchmarkRunPromptService,
)

DEFAULT_RUN_NAME = "MOON562-Progress"
DEFAULT_FIXTURE_PATH = REPO_ROOT / "system_test" / "fixtures" / "e2e_run_progress_monitor.json"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "system_test" / ".e2e-progress-run.json"


def _load_fixture(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"E2E run fixture missing: {path}")
    return json.loads(path.read_text())


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(value)


def _get_run_row(session_manager: SessionManager, run_name: str) -> tuple[int, str] | None:
    with session_manager.get_session() as session:
        row = session.execute(
            text("SELECT id, status FROM benchmark_run WHERE name = :n"),
            {"n": run_name},
        ).fetchone()
        if row is None:
            return None
        return int(row[0]), str(row[1])


def _delete_run_cascade(session_manager: SessionManager, run_id: int) -> None:
    with session_manager.get_session() as session:
        session.execute(
            text(
                "DELETE FROM benchmark_run_test_prompt WHERE run_test_id IN "
                "(SELECT id FROM benchmark_run_test_status WHERE run_id = :rid)"
            ),
            {"rid": run_id},
        )
        session.execute(
            text("DELETE FROM benchmark_run_test_status WHERE run_id = :rid"),
            {"rid": run_id},
        )
        session.execute(
            text("DELETE FROM benchmark_run_test_bundle WHERE run_id = :rid"),
            {"rid": run_id},
        )
        session.execute(text("DELETE FROM benchmark_run WHERE id = :rid"), {"rid": run_id})


def _write_manifest(manifest_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def _ensure_llm_provider(session, data: dict[str, Any]) -> int:
    row = (
        session.query(LLMProviderModel)
        .filter(
            LLMProviderModel.system_name == data["system_name"],
            LLMProviderModel.version == data["version"],
        )
        .first()
    )
    if row:
        return int(row.id)
    entity = LLMProviderModel(
        name=data["name"],
        system_name=data["system_name"],
        version=data["version"],
    )
    session.add(entity)
    session.flush()
    return int(entity.id)


def _ensure_llm_model(session, provider_id: int, data: dict[str, Any]) -> int:
    row = (
        session.query(LLMProviderModelModel)
        .filter(
            LLMProviderModelModel.llm_provider_id == provider_id,
            LLMProviderModelModel.name == data["name"],
        )
        .first()
    )
    if row:
        return int(row.id)
    entity = LLMProviderModelModel(
        llm_provider_id=provider_id,
        name=data["name"],
    )
    session.add(entity)
    session.flush()
    return int(entity.id)


def _ensure_llm_config(session, model_id: int, data: dict[str, Any]) -> int:
    row = (
        session.query(LLMProviderModelConfigModel)
        .filter(
            LLMProviderModelConfigModel.model_id == model_id,
            LLMProviderModelConfigModel.name == data["name"],
        )
        .first()
    )
    if row:
        return int(row.id)
    entity = LLMProviderModelConfigModel(
        model_id=model_id,
        name=data["name"],
        updated_dt=_parse_dt(data.get("updated_dt")) or datetime.utcnow(),
        last_used_dt=_parse_dt(data.get("last_used_dt")),
    )
    session.add(entity)
    session.flush()
    return int(entity.id)


def _ensure_config_parameters(
    session, config_id: int, parameters: list[dict[str, Any]]
) -> None:
    for param in parameters:
        existing = (
            session.query(LLMProviderModelConfigParametersModel)
            .filter(
                LLMProviderModelConfigParametersModel.config_id == config_id,
                LLMProviderModelConfigParametersModel.key == param["key"],
            )
            .first()
        )
        if existing:
            existing.value = param["value"]
        else:
            session.add(
                LLMProviderModelConfigParametersModel(
                    config_id=config_id,
                    key=param["key"],
                    value=param["value"],
                )
            )


def _ensure_metric(session, name: str) -> int:
    row = (
        session.query(BenchmarkTestMetricModel)
        .filter(BenchmarkTestMetricModel.name == name)
        .first()
    )
    if row:
        return int(row.id)
    entity = BenchmarkTestMetricModel(name=name)
    session.add(entity)
    session.flush()
    return int(entity.id)


def _ensure_dataset(session, data: dict[str, Any]) -> int:
    row = (
        session.query(BenchmarkTestDatasetModel)
        .filter(
            BenchmarkTestDatasetModel.system_name == data["system_name"],
            BenchmarkTestDatasetModel.version == data["version"],
        )
        .first()
    )
    if row:
        return int(row.id)
    entity = BenchmarkTestDatasetModel(
        version=data["version"],
        system_name=data["system_name"],
        description=data.get("description"),
        license=data.get("license"),
        reference=data.get("reference"),
    )
    session.add(entity)
    session.flush()
    return int(entity.id)


def _ensure_dataset_prompt(
    session,
    dataset_id: int,
    prompt: str,
    target: str,
) -> int:
    row = (
        session.query(BenchmarkTestDatasetPromptModel)
        .filter(
            BenchmarkTestDatasetPromptModel.benchmark_test_dataset_id == dataset_id,
            BenchmarkTestDatasetPromptModel.prompt == prompt,
            BenchmarkTestDatasetPromptModel.target == target,
        )
        .first()
    )
    if row:
        return int(row.id)
    entity = BenchmarkTestDatasetPromptModel(
        benchmark_test_dataset_id=dataset_id,
        prompt=prompt,
        target=target,
    )
    session.add(entity)
    session.flush()
    return int(entity.id)


def _ensure_bundle(session, data: dict[str, Any]) -> int:
    row = (
        session.query(BenchmarkTestBundleModel)
        .filter(
            BenchmarkTestBundleModel.system_name == data["system_name"],
            BenchmarkTestBundleModel.version == data["version"],
        )
        .first()
    )
    if row:
        return int(row.id)
    entity = BenchmarkTestBundleModel(
        version=data["version"],
        system_name=data["system_name"],
        name=data["name"],
        description=data.get("description"),
        category=data["category"],
        visible=bool(data.get("visible", True)),
    )
    session.add(entity)
    session.flush()
    return int(entity.id)


def _ensure_test(session, data: dict[str, Any], dataset_id: int, metric_id: int) -> int:
    row = (
        session.query(BenchmarkTestModel)
        .filter(
            BenchmarkTestModel.system_name == data["system_name"],
            BenchmarkTestModel.version == data["version"],
        )
        .first()
    )
    if row:
        return int(row.id)
    entity = BenchmarkTestModel(
        version=data["version"],
        system_name=data["system_name"],
        name=data["name"],
        type=data["type"],
        dataset_id=dataset_id,
        metric_id=metric_id,
        description=data.get("description"),
    )
    session.add(entity)
    session.flush()
    return int(entity.id)


def _ensure_bundle_grouping(session, bundle_id: int, test_id: int) -> None:
    row = (
        session.query(BenchmarkTestBundleGroupingModel)
        .filter(
            BenchmarkTestBundleGroupingModel.test_bundle_id == bundle_id,
            BenchmarkTestBundleGroupingModel.test_id == test_id,
        )
        .first()
    )
    if not row:
        session.add(
            BenchmarkTestBundleGroupingModel(
                test_bundle_id=bundle_id,
                test_id=test_id,
            )
        )


def _inject_fixture(session_manager: SessionManager, fixture: dict[str, Any]) -> int:
    run_name = fixture["run"]["name"]

    with session_manager.get_session() as session:
        provider_id = model_id = config_id = None
        if fixture.get("llm_provider"):
            provider_id = _ensure_llm_provider(session, fixture["llm_provider"])
        if fixture.get("llm_provider_model") and provider_id is not None:
            model_id = _ensure_llm_model(session, provider_id, fixture["llm_provider_model"])
        if fixture.get("llm_provider_model_config") and model_id is not None:
            config_id = _ensure_llm_config(
                session, model_id, fixture["llm_provider_model_config"]
            )
            _ensure_config_parameters(
                session,
                config_id,
                fixture.get("llm_provider_model_config_parameters") or [],
            )

        metric_ids = {
            m["name"]: _ensure_metric(session, m["name"])
            for m in fixture.get("benchmark_test_metrics") or []
        }
        dataset_ids = {
            (d["system_name"], d["version"]): _ensure_dataset(session, d)
            for d in fixture.get("benchmark_test_datasets") or []
        }

        dataset_prompt_ids: dict[int, int] = {}
        for dp in fixture.get("benchmark_test_dataset_prompts") or []:
            ds_key = (
                dp["benchmark_test_dataset_system_name"],
                dp["benchmark_test_dataset_version"],
            )
            ds_id = dataset_ids[ds_key]
            target_id = _ensure_dataset_prompt(
                session, ds_id, dp["prompt"], dp["target"]
            )
            dataset_prompt_ids[int(dp["source_id"])] = target_id

        bundle_ids = {
            (b["system_name"], b["version"]): _ensure_bundle(session, b)
            for b in fixture.get("benchmark_test_bundles") or []
        }
        test_ids: dict[tuple[str, int], int] = {}
        for t in fixture.get("benchmark_tests") or []:
            ds_id = dataset_ids[(t["dataset_system_name"], t["dataset_version"])]
            m_id = metric_ids[t["metric_name"]]
            test_ids[(t["system_name"], t["version"])] = _ensure_test(
                session, t, ds_id, m_id
            )

        for g in fixture.get("benchmark_test_bundle_groupings") or []:
            b_id = bundle_ids[(g["bundle_system_name"], g["bundle_version"])]
            t_id = test_ids[(g["test_system_name"], g["test_version"])]
            _ensure_bundle_grouping(session, b_id, t_id)

        run_data = fixture["run"]
        run_entity = BenchmarkRunModel(
            name=run_name,
            start_time=_parse_dt(run_data["start_time"]),
            end_time=_parse_dt(run_data.get("end_time")),
            status=run_data["status"],
            endpoint_type=run_data["endpoint_type"],
            llm_provider_id=provider_id,
            llm_provider_model_id=model_id,
            llm_provider_model_config_id=config_id,
            custom_app_id=run_data.get("custom_app_id"),
            custom_app_config_id=run_data.get("custom_app_config_id"),
        )
        session.add(run_entity)
        session.flush()
        run_id = int(run_entity.id)

        status_by_test: dict[tuple[str, int], int] = {}
        for status in fixture.get("run_test_status") or []:
            test_key = (status["test_system_name"], status["test_version"])
            test_id = test_ids[test_key]
            status_entity = BenchmarkRunTestStatusModel(
                run_id=run_id,
                test_id=test_id,
                status=status["status"],
                start_dt=_parse_dt(status.get("start_dt")),
                end_dt=_parse_dt(status.get("end_dt")),
                connector_pre_prompt=status.get("connector_pre_prompt"),
                connector_post_prompt=status.get("connector_post_prompt"),
                system_prompt=status.get("system_prompt"),
            )
            session.add(status_entity)
            session.flush()
            status_by_test[test_key] = int(status_entity.id)

        for prompt in fixture.get("run_test_prompts") or []:
            test_key = (prompt["test_system_name"], prompt["test_version"])
            run_test_id = status_by_test[test_key]
            source_prompt_id = int(prompt["source_dataset_prompt_id"])
            prompt_id = dataset_prompt_ids[source_prompt_id]
            session.add(
                BenchmarkRunTestPromptModel(
                    run_test_id=run_test_id,
                    prompt_id=prompt_id,
                    status=prompt["status"],
                    prompt_additional_info=prompt.get("prompt_additional_info"),
                    target=prompt.get("target") or "",
                    prediction_result=prompt.get("prediction_result"),
                    prediction_context=prompt.get("prediction_context"),
                    evaluation_prompt=prompt.get("evaluation_prompt"),
                    evaluation_prediction_result=prompt.get("evaluation_prediction_result"),
                    evaluation_accuracy=prompt.get("evaluation_accuracy"),
                    user_evaluation=prompt.get("user_evaluation"),
                    user_notes=prompt.get("user_notes"),
                )
            )

        for rb in fixture.get("run_test_bundle") or []:
            bundle_id = bundle_ids[(rb["bundle_system_name"], rb["bundle_version"])]
            test_id = test_ids[(rb["test_system_name"], rb["test_version"])]
            session.add(
                BenchmarkRunTestBundleModel(
                    run_id=run_id,
                    test_bundle_id=bundle_id,
                    test_id=test_id,
                )
            )

        return run_id


def seed_running_progress_run(
    *,
    run_name: str | None = None,
    fixture_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """
    Inject the in-progress fixture run into MOONSHOT_DB_PATH and return manifest metadata.
    """
    fixture_path = fixture_path or Path(
        os.environ.get("E2E_PROGRESS_RUN_FIXTURE_PATH", str(DEFAULT_FIXTURE_PATH))
    )
    manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
    fixture = _load_fixture(fixture_path)
    run_name = run_name or fixture["run"]["name"]

    session_manager = SessionManager.get_instance()
    existing = _get_run_row(session_manager, run_name)
    if existing is not None:
        run_id, status = existing
        if status == "running":
            prompts = BenchmarkRunPromptService().get_all_prompts_by_run_id(run_id)
            return _write_manifest(
                manifest_path,
                {
                    "runId": run_id,
                    "runName": run_name,
                    "expectedPromptCount": len(prompts),
                },
            )
        _delete_run_cascade(session_manager, run_id)

    run_id = _inject_fixture(session_manager, fixture)
    prompts = BenchmarkRunPromptService().get_all_prompts_by_run_id(run_id)
    return _write_manifest(
        manifest_path,
        {
            "runId": run_id,
            "runName": run_name,
            "expectedPromptCount": len(prompts),
        },
    )


def main() -> int:
    db_path = os.environ.get("MOONSHOT_DB_PATH")
    if not db_path:
        print("error: MOONSHOT_DB_PATH must be set", file=sys.stderr)
        return 1
    os.chdir(MOONSHOT_CORE_ROOT)
    SessionManager.reset_instance()
    try:
        manifest = seed_running_progress_run()
    except Exception as exc:
        print(f"error: seed failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"Seeded running run {manifest['runName']!r} "
        f"(id={manifest['runId']}, prompts={manifest['expectedPromptCount']})"
    )
    print(f"Manifest: {DEFAULT_MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
