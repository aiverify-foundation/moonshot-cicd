"""
Integration test for run_benchmark happy path with DB.

Seeds config, creates a benchmark run and run_test with prompts, then runs
run_benchmark with write_to_db=True. Mocks connector and metric so no real
LLM calls. Asserts run_test_status becomes completed and run_test_prompts
get prediction_result and evaluation fields updated.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestPromptModel,
    BenchmarkRunTestStatusModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from application.services.benchmark_run_test_setup_service import (
    BenchmarkRunTestSetupService,
)
from application.services.shared_config_seed_service import SharedConfigSeedService
from application.services.file_shared_config_repository import (
    FileSharedConfigRepository,
)
from application.services.file_dataset_repository import FileDatasetRepository
from application.services.benchmark_dataset_seed_service import (
    BenchmarkDatasetSeedService,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (
    MoonshotConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.dataset_adapter import (
    SqlAlchemyDatasetRepository,
)
from domain.services.task_manager import TaskManager
from domain.services.enums.module_types import ModuleTypes
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity


@pytest.fixture(scope="session")
def test_db_path():
    """Database path for integration tests. Cleaned once at session start; shared by all tests."""
    moonshot_core_root = Path(__file__).resolve().parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_run_benchmark.db"
    if db_path.exists():
        db_path.unlink()
    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set MOONSHOT_DB_PATH and reset SessionManager."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def config_path():
    """Path to shared config with minimal bundle and one test."""
    return (
        Path(__file__).resolve().parent
        / "fixtures"
        / "shared_minimal_two_tests.yaml"
    )


@pytest.fixture
def shared_config_seed_service(test_db_env):
    """Build SharedConfigSeedService for seeding."""
    shared_config_repo = FileSharedConfigRepository()
    file_dataset_repo = FileDatasetRepository()
    moonshot_config = MoonshotConfigAdapter()
    sqlalchemy_dataset_repo = SqlAlchemyDatasetRepository()
    dataset_seed_service = BenchmarkDatasetSeedService(
        source_dataset_repository=file_dataset_repo,
        target_dataset_repository=sqlalchemy_dataset_repo,
    )
    return SharedConfigSeedService(
        moonshot_config_repository=moonshot_config,
        shared_config_repository=shared_config_repo,
        benchmark_dataset_seed_service=dataset_seed_service,
    )


def _insert_benchmark_run(session_manager, name: str) -> int:
    """Insert a benchmark_run row via raw SQL; return the new run id."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with session_manager.get_session() as session:
        session.execute(
            text("""
                INSERT INTO benchmark_run (name, status, endpoint_type, start_time)
                VALUES (:name, :status, :endpoint_type, :start_time)
            """),
            {
                "name": name,
                "status": "running",
                "endpoint_type": "LLM_Provider",
                "start_time": now,
            },
        )
        session.flush()
        (run_id,) = session.execute(text("SELECT last_insert_rowid()")).fetchone()
        return run_id


def _seed_and_get_run_and_test_id(shared_config_seed_service, config_path, session_manager, run_name: str):
    """Seed from config if needed, insert one run, return (run_id, test_id)."""
    shared_config_seed_service.seed_if_test_file_changed(config_path=config_path)
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 1
    run_id = _insert_benchmark_run(session_manager, run_name)
    return run_id, test_ids[0]


def _get_run_test_status(session_manager, run_id: int, test_id: int):
    """Return (status, end_dt) for the benchmark_run_test_status row, or (None, None)."""
    with session_manager.get_session() as session:
        row = (
            session.query(BenchmarkRunTestStatusModel)
            .filter(
                BenchmarkRunTestStatusModel.run_id == run_id,
                BenchmarkRunTestStatusModel.test_id == test_id,
            )
            .first()
        )
        if row is None:
            return None, None
        return row.status, row.end_dt


def _get_run_test_prompts(session_manager, run_test_id: int):
    """Return list of (prediction_result, evaluation_prediction_result, evaluation_accuracy) for the run_test_id."""
    with session_manager.get_session() as session:
        rows = (
            session.query(BenchmarkRunTestPromptModel)
            .filter(BenchmarkRunTestPromptModel.run_test_id == run_test_id)
            .order_by(BenchmarkRunTestPromptModel.id)
            .all()
        )
        return [
            (r.prediction_result, r.evaluation_prediction_result, r.evaluation_accuracy)
            for r in rows
        ]


def _assert_run_test_completed(
    session_manager,
    run_id: int,
    test_id: int,
    run_test_id: int,
    expected_prediction: str = "integration test response",
):
    """Assert the run_test (run_id, test_id) is completed and its prompts have results."""
    status, end_dt = _get_run_test_status(session_manager, run_id, test_id)
    assert status is not None
    assert status == "completed"
    assert end_dt is not None
    prompt_rows = _get_run_test_prompts(session_manager, run_test_id)
    assert len(prompt_rows) >= 1
    for prediction_result, evaluation_prediction_result, evaluation_accuracy in prompt_rows:
        assert prediction_result is not None
        assert prediction_result == expected_prediction
        assert evaluation_prediction_result is not None
        assert evaluation_accuracy is not None


def _seed_and_get_run_and_test_ids(
    shared_config_seed_service,
    config_path,
    session_manager,
    run_name: str,
    min_tests: int = 1,
):
    """Seed from config if needed, insert one run, return (run_id, test_ids list)."""
    shared_config_seed_service.seed_if_test_file_changed(config_path=config_path)
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= min_tests
    run_id = _insert_benchmark_run(session_manager, run_name)
    return run_id, test_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_benchmark_happy_path_write_to_db(
    shared_config_seed_service,
    test_db_env,
    config_path,
):
    """
    Happy path: seed config, create run + run_test with prompts, run run_benchmark
    with write_to_db=True; assert status is completed and prompts have results.
    """
    assert config_path.exists()
    session_manager = SessionManager.get_instance()
    run_id, test_id = _seed_and_get_run_and_test_id(
        shared_config_seed_service,
        config_path,
        session_manager,
        "integration-run-benchmark-happy",
    )

    setup_service = BenchmarkRunTestSetupService()
    status, prompts = setup_service.create_run_test_with_prompts(run_id, test_id)
    assert status.status == "not_started"
    assert len(prompts) >= 1
    run_test_id = status.id

    # Mock connector: return a ConnectorEntity and make ModuleLoader return a mock adapter
    mock_connector_instance = MagicMock()
    mock_connector_instance.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response="integration test response", context=[])
    )
    mock_connector_instance.configure = MagicMock()

    mock_metric_instance = MagicMock()
    mock_metric_instance.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric_instance.get_results = AsyncMock(return_value={})
    mock_metric_instance.update_metric_params = MagicMock()

    connector_entity = ConnectorEntity(
        connector_adapter="mock_integration_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader
    from adapters.prompt_processor.asyncio_prompt_processor_adapter import AsyncioPromptProcessor

    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_integration_connector":
            return (mock_connector_instance, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric_instance, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    task_manager = TaskManager()
    # _load_module is called: 1) dataset, 2) prompt_processor, 3) metric (in _convert_prompt_entities_to_dicts)
    mock_metric_for_convert = MagicMock()
    with (
        patch.object(task_manager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            task_manager,
            "_load_module",
            side_effect=[
                MagicMock(),  # dataset (not used when prompts from DB)
                (AsyncioPromptProcessor(), "asyncio_pp"),
                (mock_metric_for_convert, "refusal_adapter"),  # metric for result conversion
            ],
        ),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch(
            "domain.services.task_manager.AppConfig",
        ) as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        result = await task_manager.run_benchmark(
            run_id=str(run_id),
            test_name="Sample Test",
            dataset="test_sample_dataset",
            metric={"name": "refusal_adapter"},
            connector="mock_integration_connector",
            prompt_processor="asyncio_prompt_processor_adapter",
            callback_fn=None,
            write_result=False,
            write_to_db=True,
            db_run_id=run_id,
            test_id=test_id,
        )

    assert result != ""
    _assert_run_test_completed(session_manager, run_id, test_id, run_test_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_benchmark_twice_two_runs_updates_both(
    shared_config_seed_service,
    test_db_env,
    config_path,
):
    """
    Run benchmark twice with two separate run_ids; assert both runs are
    completed and their prompts updated.
    """
    assert config_path.exists()
    session_manager = SessionManager.get_instance()
    run_id_1, test_ids = _seed_and_get_run_and_test_ids(
        shared_config_seed_service,
        config_path,
        session_manager,
        "integration-run-benchmark-twice-1",
        min_tests=1,
    )
    test_id = test_ids[0]

    setup_service = BenchmarkRunTestSetupService()
    status_1, _ = setup_service.create_run_test_with_prompts(run_id_1, test_id)
    assert status_1.status == "not_started"
    run_test_id_1 = status_1.id

    run_id_2 = _insert_benchmark_run(session_manager, "integration-run-benchmark-twice-2")
    status_2, _ = setup_service.create_run_test_with_prompts(run_id_2, test_id)
    assert status_2.status == "not_started"
    run_test_id_2 = status_2.id

    mock_connector_instance = MagicMock()
    mock_connector_instance.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response="integration test response", context=[])
    )
    mock_connector_instance.configure = MagicMock()
    mock_metric_instance = MagicMock()
    mock_metric_instance.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric_instance.get_results = AsyncMock(return_value={})
    mock_metric_instance.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_integration_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader
    from adapters.prompt_processor.asyncio_prompt_processor_adapter import AsyncioPromptProcessor

    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_integration_connector":
            return (mock_connector_instance, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric_instance, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    task_manager = TaskManager()
    mock_metric_for_convert = MagicMock()
    # Two runs: each run_benchmark uses 3 _load_module calls (dataset, prompt_processor, metric)
    load_module_side_effect = []
    for _ in range(2):
        load_module_side_effect.append(MagicMock())
        load_module_side_effect.append((AsyncioPromptProcessor(), "asyncio_pp"))
        load_module_side_effect.append((mock_metric_for_convert, "refusal_adapter"))

    with (
        patch.object(task_manager, "_get_connector_config", return_value=connector_entity),
        patch.object(task_manager, "_load_module", side_effect=load_module_side_effect),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config

        result_1 = await task_manager.run_benchmark(
            run_id=str(run_id_1),
            test_name="Sample Test",
            dataset="test_sample_dataset",
            metric={"name": "refusal_adapter"},
            connector="mock_integration_connector",
            prompt_processor="asyncio_prompt_processor_adapter",
            callback_fn=None,
            write_result=False,
            write_to_db=True,
            db_run_id=run_id_1,
            test_id=test_id,
        )
        assert result_1 != ""
        _assert_run_test_completed(session_manager, run_id_1, test_id, run_test_id_1)

        result_2 = await task_manager.run_benchmark(
            run_id=str(run_id_2),
            test_name="Sample Test",
            dataset="test_sample_dataset",
            metric={"name": "refusal_adapter"},
            connector="mock_integration_connector",
            prompt_processor="asyncio_prompt_processor_adapter",
            callback_fn=None,
            write_result=False,
            write_to_db=True,
            db_run_id=run_id_2,
            test_id=test_id,
        )
        assert result_2 != ""
        _assert_run_test_completed(session_manager, run_id_2, test_id, run_test_id_2)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_benchmark_two_runs_two_tests_both_updated(
    shared_config_seed_service,
    test_db_env,
    config_path,
):
    """
    Same run_id, two tests: run run_benchmark for (run_id, test_id_1) then
    (run_id, test_id_2); assert both run_test_status rows and their prompts are updated.
    """
    assert config_path.exists()
    session_manager = SessionManager.get_instance()
    run_id, test_ids = _seed_and_get_run_and_test_ids(
        shared_config_seed_service,
        config_path,
        session_manager,
        "integration-run-benchmark-same-run-two-tests",
        min_tests=2,
    )
    test_id_1, test_id_2 = test_ids[0], test_ids[1]

    setup_service = BenchmarkRunTestSetupService()
    status_1, _ = setup_service.create_run_test_with_prompts(run_id, test_id_1)
    assert status_1.status == "not_started"
    run_test_id_1 = status_1.id
    status_2, _ = setup_service.create_run_test_with_prompts(run_id, test_id_2)
    assert status_2.status == "not_started"
    run_test_id_2 = status_2.id

    mock_connector_instance = MagicMock()
    mock_connector_instance.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response="integration test response", context=[])
    )
    mock_connector_instance.configure = MagicMock()
    mock_metric_instance = MagicMock()
    mock_metric_instance.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric_instance.get_results = AsyncMock(return_value={})
    mock_metric_instance.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_integration_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader
    from adapters.prompt_processor.asyncio_prompt_processor_adapter import AsyncioPromptProcessor

    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_integration_connector":
            return (mock_connector_instance, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric_instance, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    task_manager = TaskManager()
    mock_metric_for_convert = MagicMock()
    load_module_side_effect = []
    for _ in range(2):
        load_module_side_effect.append(MagicMock())
        load_module_side_effect.append((AsyncioPromptProcessor(), "asyncio_pp"))
        load_module_side_effect.append((mock_metric_for_convert, "refusal_adapter"))

    with (
        patch.object(task_manager, "_get_connector_config", return_value=connector_entity),
        patch.object(task_manager, "_load_module", side_effect=load_module_side_effect),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config

        result_1 = await task_manager.run_benchmark(
            run_id=str(run_id),
            test_name="Sample Test",
            dataset="test_sample_dataset",
            metric={"name": "refusal_adapter"},
            connector="mock_integration_connector",
            prompt_processor="asyncio_prompt_processor_adapter",
            callback_fn=None,
            write_result=False,
            write_to_db=True,
            db_run_id=run_id,
            test_id=test_id_1,
        )
        assert result_1 != ""
        _assert_run_test_completed(session_manager, run_id, test_id_1, run_test_id_1)

        result_2 = await task_manager.run_benchmark(
            run_id=str(run_id),
            test_name="Second Test",
            dataset="test_sample_dataset",
            metric={"name": "refusal_adapter"},
            connector="mock_integration_connector",
            prompt_processor="asyncio_prompt_processor_adapter",
            callback_fn=None,
            write_result=False,
            write_to_db=True,
            db_run_id=run_id,
            test_id=test_id_2,
        )
        assert result_2 != ""
        _assert_run_test_completed(session_manager, run_id, test_id_2, run_test_id_2)
