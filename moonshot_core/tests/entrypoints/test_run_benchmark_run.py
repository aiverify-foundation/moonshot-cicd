"""
Tests for benchmark run entrypoints (DB-backed ``start_benchmark_run`` and YAML ``execute_bundle``).

- ``test_run_benchmark_run_with_test_prompts_bundle``: relational FK trio + ``start_benchmark_run``;
  ``DatabaseConnectorConfigService.build_connector_entity`` is mocked (real DB rows are not the
  source of the connector module). In-process ``fake_process`` avoids subprocess/event-loop issues.
- ``test_execute_bundle_yaml_connector_path``: ``execute_bundle`` with a YAML connector id only
  (no ``llm_provider_*``); ``TaskManager._get_connector_config`` is mocked.

Connector execution is mocked (no real OpenAI). Uses tests/entrypoints/conftest.py seed.
"""

import json
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.benchmark_execution_service import BenchmarkExecutionService
from application.services.database_connector_config_service import (
    DatabaseConnectorConfigService,
)
from application.services.provider_seed_service import ProviderSeedService
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.services.app_config import AppConfig
from domain.services.enums.module_types import ModuleTypes
from domain.services.task_manager import TaskManager


BUNDLE_NAME = "test-prompts"


def _ensure_relational_openai_benchmark_ids() -> tuple[int, int, int]:
    """Seed providers and ensure one OpenAI model + model_config row for benchmark_run FKs."""
    ProviderSeedService().seed_hardcoded_providers()
    session_manager = SessionManager.get_instance()
    with session_manager.get_session() as session:
        provider = (
            session.query(LLMProviderModel)
            .filter(LLMProviderModel.system_name == "openai_adapter")
            .order_by(LLMProviderModel.id.desc())
            .first()
        )
        assert provider is not None, "Expected seeded llm_provider for openai_adapter"
        model = (
            session.query(LLMProviderModelModel)
            .filter(
                LLMProviderModelModel.llm_provider_id == provider.id,
                LLMProviderModelModel.name == "gpt-4o-mini",
            )
            .first()
        )
        if model is None:
            model = LLMProviderModelModel(
                llm_provider_id=provider.id,
                name="gpt-4o-mini",
            )
            session.add(model)
            session.flush()
        cfg = (
            session.query(LLMProviderModelConfigModel)
            .filter(LLMProviderModelConfigModel.model_id == model.id)
            .first()
        )
        if cfg is None:
            cfg = LLMProviderModelConfigModel(
                model_id=model.id,
                name="pytest-entrypoint-default",
            )
            session.add(cfg)
            session.flush()
        session.commit()
        return int(provider.id), int(model.id), int(cfg.id)


def _make_load_module_side_effect(num_tests: int):
    """Three _load_module results per test: dataset, prompt_processor, metric."""
    from adapters.prompt_processor.asyncio_prompt_processor_adapter import AsyncioPromptProcessor

    mock_metric = MagicMock()
    return [
        MagicMock(),
        (AsyncioPromptProcessor(), "asyncio_pp"),
        (mock_metric, "refusal_adapter"),
    ] * num_tests


def _wait_for_result_file(absolute_result_path: Path, max_wait: float = 15) -> dict:
    """Wait for result file to appear and return parsed JSON (blocking)."""
    wait_interval = 0.2
    waited = 0.0
    while waited < max_wait:
        if absolute_result_path.exists():
            break
        time.sleep(wait_interval)
        waited += wait_interval

    assert absolute_result_path.exists(), (
        f"Result file not created after {waited:.1f}s. Expected: {absolute_result_path}"
    )

    with open(absolute_result_path, "r") as f:
        return json.load(f)


def test_run_benchmark_run_with_test_prompts_bundle(
    seed_shared_config,
    test_db_env,
    tmp_path,
):
    """
    DB connector path: relational FK trio + ``start_benchmark_run`` (same as
    ``POST /api/start-benchmark-run``). ``build_connector_entity`` is mocked to a fake connector;
    worker runs in-process via patched ``Process``.
    """
    result_file = tmp_path / f"{BUNDLE_NAME}.json"
    if result_file.exists():
        result_file.unlink()

    llm_provider_id, llm_provider_model_id, llm_provider_model_config_id = (
        _ensure_relational_openai_benchmark_ids()
    )

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_db_id = config_adapter.get_bundle_id_by_system_name_latest(BUNDLE_NAME)
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_db_id)
    assert len(test_ids) >= 1
    num_tests = len(test_ids)

    run_name = f"entrypoint-test-run-{uuid.uuid4().hex[:12]}"
    expected_prediction = "entrypoint start-benchmark-run mock response"

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response=expected_prediction, context=[])
    )
    mock_connector.configure = MagicMock()

    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()

    connector_entity = ConnectorEntity(
        connector_adapter="mock_entrypoint_benchmark_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_load = ModuleLoader.load

    def mock_load_module_impl(module_name, module_type):
        if (
            module_type == ModuleTypes.CONNECTOR
            and module_name == "mock_entrypoint_benchmark_connector"
        ):
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC:
            return (mock_metric, module_name)
        return real_load(module_name, module_type)

    def fake_process(*, target=None, args=(), **kwargs):
        fake = MagicMock()

        def start():
            if target is not None:
                target(*args)

        fake.start = start
        return fake

    payload = {
        "run_name": run_name,
        "bundle_names": [BUNDLE_NAME],
        "llm_provider_id": llm_provider_id,
        "llm_provider_model_id": llm_provider_model_id,
        "llm_provider_model_config_id": llm_provider_model_config_id,
    }

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(
            DatabaseConnectorConfigService,
            "build_connector_entity",
            return_value=connector_entity,
        ),
        patch.object(
            TaskManager,
            "_load_module",
            side_effect=_make_load_module_side_effect(num_tests),
        ),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module_impl),
        patch(
            "application.services.benchmark_execution_service.multiprocessing.Process",
            side_effect=fake_process,
        ),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)

        BenchmarkExecutionService().start_benchmark_run(
            run_name=run_name,
            bundle_names=[BUNDLE_NAME],
            llm_provider_id=payload["llm_provider_id"],
            llm_provider_model_id=payload["llm_provider_model_id"],
            llm_provider_model_config_id=payload["llm_provider_model_config_id"],
        )

    result_data = _wait_for_result_file(result_file, max_wait=15)

    assert "run_metadata" in result_data
    assert "run_results" in result_data
    assert len(result_data["run_results"]) >= 1
    assert result_data["run_metadata"]["test_id"] == BUNDLE_NAME


def test_execute_bundle_yaml_connector_path(seed_shared_config, test_db_env, tmp_path):
    """
    YAML connector path: ``execute_bundle`` with ``connector=`` only (no DB llm_provider* ids).
    ``TaskManager._get_connector_config`` is mocked; no subprocess.
    """
    result_file = tmp_path / f"{BUNDLE_NAME}.json"
    if result_file.exists():
        result_file.unlink()

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_db_id = config_adapter.get_bundle_id_by_system_name_latest(BUNDLE_NAME)
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_db_id)
    assert len(test_ids) >= 1
    num_tests = len(test_ids)

    expected_prediction = "entrypoint yaml connector mock response"

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response=expected_prediction, context=[])
    )
    mock_connector.configure = MagicMock()

    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()

    connector_entity = ConnectorEntity(
        connector_adapter="mock_entrypoint_benchmark_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_load = ModuleLoader.load

    def mock_load_module_impl(module_name, module_type):
        if (
            module_type == ModuleTypes.CONNECTOR
            and module_name == "mock_entrypoint_benchmark_connector"
        ):
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC:
            return (mock_metric, module_name)
        return real_load(module_name, module_type)

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager,
            "_load_module",
            side_effect=_make_load_module_side_effect(num_tests),
        ),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module_impl),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)

        BenchmarkExecutionService().execute_bundle(
            BUNDLE_NAME,
            connector="my-gpt-4o-mini",
            write_to_db=False,
        )

    result_data = _wait_for_result_file(result_file, max_wait=15)
    assert "run_metadata" in result_data
    assert "run_results" in result_data
    assert len(result_data["run_results"]) >= 1
    assert result_data["run_metadata"]["test_id"] == BUNDLE_NAME
