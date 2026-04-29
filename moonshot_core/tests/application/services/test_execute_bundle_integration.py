"""
Integration test for execute_bundle happy path with real database.

Seeds config (minimal-bundle), creates a benchmark run, populates benchmark_run_test_bundle
via BenchmarkRunTestBundlePopulationService, then calls execute_bundle with write_to_db=True
so it uses the DB path (creates run_test + prompts, runs run_benchmark).
Mocks connector and metric so no real LLM calls. Asserts result file and DB state
(run_test_status completed, prompts have prediction and evaluation).
"""

import os
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
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
from application.services.benchmark_run_test_bundle_population_service import (
    BenchmarkRunTestBundlePopulationService,
)
from application.services.benchmark_execution_service import BenchmarkExecutionService
from application.services.benchmark_run_prompt_service import (
    BenchmarkRunPromptService,
)
from application.services.benchmark_run_service import BenchmarkRunService
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
from domain.services.app_config import AppConfig
from domain.services.task_manager import TaskManager
from domain.services.enums.module_types import ModuleTypes
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity

# Ensure src is on path for entrypoints.api when running this module
_src_path = Path(__file__).resolve().parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from entrypoints.api import app as fastapi_app

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
CONFIG_PATH = FIXTURES_DIR / "shared_minimal.yaml"
CONFIG_PATH_TWO_TESTS = FIXTURES_DIR / "shared_minimal_two_tests.yaml"


@pytest.fixture(scope="session")
def test_db_path():
    """Shared database path for this module; cleared once at session start."""
    moonshot_core_root = Path(__file__).resolve().parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_execute_bundle.db"
    if db_path.exists():
        db_path.unlink()
    return str(db_path)


@pytest.fixture(scope="session")
def test_db_env(test_db_path):
    """Set MOONSHOT_DB_PATH and reset SessionManager (session-scoped, DB not cleared per test)."""
    old_val = os.environ.get("MOONSHOT_DB_PATH")
    os.environ["MOONSHOT_DB_PATH"] = test_db_path
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    if old_val is not None:
        os.environ["MOONSHOT_DB_PATH"] = old_val
    else:
        os.environ.pop("MOONSHOT_DB_PATH", None)


@pytest.fixture(scope="session")
def shared_config_seed_service(test_db_env):
    """Build SharedConfigSeedService for seeding (session-scoped)."""
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
    """Insert a benchmark_run row; return the new run id."""
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


def _get_run_test_status(session_manager, run_id: int, test_id: int):
    """Return (run_test_id, status, end_dt) for (run_id, test_id), or (None, None, None)."""
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
            return None, None, None
        return row.id, row.status, row.end_dt


def _get_run_test_prompts(session_manager, run_test_id: int):
    """Return list of (prediction_result, evaluation_prediction_result, evaluation_accuracy)."""
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


def _make_load_module_side_effect(num_tests: int):
    """Build _load_module side_effect list: 3 items per run_benchmark (dataset, prompt_processor, metric)."""
    from adapters.prompt_processor.asyncio_prompt_processor_adapter import AsyncioPromptProcessor
    mock_metric = MagicMock()
    return [
        MagicMock(),
        (AsyncioPromptProcessor(), "asyncio_pp"),
        (mock_metric, "refusal_adapter"),
    ] * num_tests




@pytest.mark.integration
def test_execute_bundle_happy_path_with_db(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Happy path: seed config, create run, call execute_bundle with write_to_db=True.
    execute_bundle uses DB path (creates run_test + prompts, run_benchmark). Mock connector
    and metric. Assert result file exists and DB run_test status is completed with prompt results.
    """
    assert CONFIG_PATH.exists(), f"Fixture config missing: {CONFIG_PATH}"

    shared_config_seed_service.seed_if_test_file_changed(config_path=CONFIG_PATH)
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 1

    session_manager = SessionManager.get_instance()
    run_id = _insert_benchmark_run(session_manager, "execute-bundle-integration-run")

    pop_service = BenchmarkRunTestBundlePopulationService()
    pop_service.populate_run_bundle(run_id, "minimal-bundle")

    # Mock connector and metric (no real LLM)
    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response="execute_bundle db test response", context=[])
    )
    mock_connector.configure = MagicMock()

    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()

    connector_entity = ConnectorEntity(
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader
    from adapters.prompt_processor.asyncio_prompt_processor_adapter import AsyncioPromptProcessor

    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_execute_bundle_connector":
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager,
            "_load_module",
            side_effect=_make_load_module_side_effect(1),
        ),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch(
            "domain.services.task_manager.AppConfig",
        ) as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)

        service = BenchmarkExecutionService()
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=run_id,
            write_to_db=True,
        )

    # Assert result file
    result_file = tmp_path / "minimal-bundle.json"
    assert result_file.exists(), f"Expected result file at {result_file}"
    data = json.loads(result_file.read_text())
    assert "run_metadata" in data
    assert "run_results" in data
    assert len(data["run_results"]) >= 1
    assert "start_time" in data["run_metadata"] and "end_time" in data["run_metadata"]

    # Assert DB: each test's run_test_status is completed and prompts have results
    _assert_run_completed(session_manager, run_id, test_ids, "execute_bundle db test response")


def _assert_run_completed(session_manager, run_id: int, test_ids: list, expected_prediction: str):
    """Assert all tests for run_id are completed with prompt results."""
    for test_id in test_ids:
        run_test_id, status, end_dt = _get_run_test_status(session_manager, run_id, test_id)
        assert run_test_id is not None, f"run_test_status missing for run_id={run_id}, test_id={test_id}"
        assert status == "completed"
        assert end_dt is not None
        prompts = _get_run_test_prompts(session_manager, run_test_id)
        assert len(prompts) >= 1
        for prediction_result, evaluation_prediction_result, evaluation_accuracy in prompts:
            assert prediction_result is not None
            assert prediction_result == expected_prediction
            assert evaluation_prediction_result is not None
            assert evaluation_accuracy is not None


@pytest.mark.integration
def test_execute_bundle_two_runs_back_to_back(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Run execute_bundle twice (two separate runs) back to back; DB is not cleared between.
    Assert both runs have completed run_test_status and prompt results.
    """
    assert CONFIG_PATH.exists()
    shared_config_seed_service.seed_if_test_file_changed(config_path=CONFIG_PATH)
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 1

    session_manager = SessionManager.get_instance()

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response="two-runs response", context=[])
    )
    mock_connector.configure = MagicMock()
    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader
    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_execute_bundle_connector":
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    # 2 runs × 1 test × 3 _load_module calls = 6
    load_side_effect = _make_load_module_side_effect(2)
    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(TaskManager, "_load_module", side_effect=load_side_effect),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)
        service = BenchmarkExecutionService()

        run_id_1 = _insert_benchmark_run(session_manager, "execute-bundle-run-1")
        BenchmarkRunTestBundlePopulationService().populate_run_bundle(run_id_1, "minimal-bundle")
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=run_id_1,
            write_to_db=True,
        )

        run_id_2 = _insert_benchmark_run(session_manager, "execute-bundle-run-2")
        BenchmarkRunTestBundlePopulationService().populate_run_bundle(run_id_2, "minimal-bundle")
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=run_id_2,
            write_to_db=True,
        )

    # Result file exists (second run overwrote first)
    result_file = tmp_path / "minimal-bundle.json"
    assert result_file.exists()
    data = json.loads(result_file.read_text())
    assert len(data["run_results"]) >= 1

    _assert_run_completed(session_manager, run_id_1, test_ids, "two-runs response")
    _assert_run_completed(session_manager, run_id_2, test_ids, "two-runs response")


@pytest.mark.integration
def test_execute_bundle_bundle_with_two_tests(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Run execute_bundle for a bundle that contains two tests (shared_minimal_two_tests.yaml).
    Assert result file has two run_results and DB has both tests completed.
    """
    assert CONFIG_PATH_TWO_TESTS.exists(), f"Fixture missing: {CONFIG_PATH_TWO_TESTS}"
    shared_config_seed_service.seed_if_test_file_changed(config_path=CONFIG_PATH_TWO_TESTS)
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 2

    session_manager = SessionManager.get_instance()
    run_id = _insert_benchmark_run(session_manager, "execute-bundle-two-tests-run")
    BenchmarkRunTestBundlePopulationService().populate_run_bundle(run_id, "minimal-bundle")

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response="two-tests response", context=[])
    )
    mock_connector.configure = MagicMock()
    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader
    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_execute_bundle_connector":
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    # 2 tests run sequentially; 2 × 3 _load_module calls = 6
    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(TaskManager, "_load_module", side_effect=_make_load_module_side_effect(2)),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)
        service = BenchmarkExecutionService()
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=run_id,
            write_to_db=True,
        )

    # Assert DB: both tests in the bundle completed with prompt results
    _assert_run_completed(session_manager, run_id, test_ids, "two-tests response")
    # Assert result file when present (path can vary by environment)
    result_file = tmp_path / "minimal-bundle.json"
    if result_file.exists():
        data = json.loads(result_file.read_text())
        assert "run_results" in data
        assert len(data["run_results"]) == 2


@pytest.mark.integration
def test_execute_bundle_duplicate_run_name_no_new_run(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    When the run name would be duplicated (e.g. "Bundle run: minimal-bundle"),
    execute_bundle must not create a new run; it must reuse the existing run.
    We create a run with that name first, then call execute_bundle with run_id=None
    twice; the second call must not create another run.
    """
    assert CONFIG_PATH.exists()
    shared_config_seed_service.seed_if_test_file_changed(config_path=CONFIG_PATH)
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 1

    from application.services.benchmark_run_service import BenchmarkRunService

    session_manager = SessionManager.get_instance()
    run_name = "Bundle run: minimal-bundle"
    # Create the run that execute_bundle would use when run_id is None (same name)
    run_id_created = _insert_benchmark_run(session_manager, run_name)
    BenchmarkRunTestBundlePopulationService().populate_run_bundle(run_id_created, "minimal-bundle")

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response="dup-name response", context=[])
    )
    mock_connector.configure = MagicMock()
    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader
    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_execute_bundle_connector":
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    # 2 calls × 1 test × 3 _load_module = 6
    load_side_effect = _make_load_module_side_effect(2)
    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(TaskManager, "_load_module", side_effect=load_side_effect),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)
        service = BenchmarkExecutionService()

        # First call with run_id=None: must reuse existing run (no new run)
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=None,
            write_to_db=True,
        )
        run_after_first = BenchmarkRunService().get_run_by_name(run_name)
        assert run_after_first is not None
        assert run_after_first.id == run_id_created, (
            "First execute_bundle with run_id=None must reuse existing run with same name"
        )

        # Second call with run_id=None: must still be the same run (no new run)
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=None,
            write_to_db=True,
        )
        run_after_second = BenchmarkRunService().get_run_by_name(run_name)
        assert run_after_second is not None
        assert run_after_second.id == run_id_created, (
            "Duplicate run name must not create a new run; expected same run_id"
        )

    # Only one run with that name in the DB
    from adapters.driven.repository.sqlalchemy.benchmark_run_adapter import (
        SqlAlchemyBenchmarkRunRepository,
    )
    repo = SqlAlchemyBenchmarkRunRepository()
    runs_with_name = [r for r in repo.get_all() if r.name == run_name]
    assert len(runs_with_name) == 1, (
        f"Expected exactly one run with name {run_name!r}, got {len(runs_with_name)}"
    )
    assert runs_with_name[0].id == run_id_created


@pytest.mark.integration
def test_execute_bundle_then_get_all_prompts_by_run_id(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Run execute_bundle for a bundle with two tests, then get_all_prompts_by_run_id
    returns all prompts for the run with prediction and evaluation set.
    """
    assert CONFIG_PATH_TWO_TESTS.exists(), f"Fixture missing: {CONFIG_PATH_TWO_TESTS}"
    shared_config_seed_service.seed_if_test_file_changed(
        config_path=CONFIG_PATH_TWO_TESTS
    )
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 2

    session_manager = SessionManager.get_instance()
    run_id = _insert_benchmark_run(
        session_manager, "integration-get-prompts-after-execute"
    )
    BenchmarkRunTestBundlePopulationService().populate_run_bundle(
        run_id, "minimal-bundle"
    )

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(
            response="get-prompts-after-execute response", context=[]
        )
    )
    mock_connector.configure = MagicMock()
    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if (
            module_type == ModuleTypes.CONNECTOR
            and module_name == "mock_execute_bundle_connector"
        ):
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager, "_load_module", side_effect=_make_load_module_side_effect(2)
        ),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)
        service = BenchmarkExecutionService()
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=run_id,
            write_to_db=True,
        )

    _assert_run_completed(
        session_manager, run_id, test_ids, "get-prompts-after-execute response"
    )

    prompt_service = BenchmarkRunPromptService()
    result = prompt_service.get_all_prompts_by_run_id(run_id)

    assert len(result) >= 2
    for entity in result:
        assert entity.id is not None
        assert entity.run_test_id is not None
        assert entity.prompt_id is not None
        assert entity.prediction_result is not None
        assert entity.evaluation_prediction_result is not None
        assert entity.evaluation_accuracy is not None


@pytest.mark.integration
def test_get_benchmark_run_prompts_api(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    GET /api/benchmark-runs/{run_id}/prompts returns all prompts for the run after execute_bundle.

    Runs execute_bundle with a real DB and mocks, then calls the API and asserts
    response shape and content.
    """
    assert CONFIG_PATH_TWO_TESTS.exists(), f"Fixture missing: {CONFIG_PATH_TWO_TESTS}"
    shared_config_seed_service.seed_if_test_file_changed(
        config_path=CONFIG_PATH_TWO_TESTS
    )
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 2

    session_manager = SessionManager.get_instance()
    run_id = _insert_benchmark_run(
        session_manager, "integration-get-prompts-api"
    )
    BenchmarkRunTestBundlePopulationService().populate_run_bundle(
        run_id, "minimal-bundle"
    )

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(
            response="get-prompts-api response", context=[]
        )
    )
    mock_connector.configure = MagicMock()
    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if (
            module_type == ModuleTypes.CONNECTOR
            and module_name == "mock_execute_bundle_connector"
        ):
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager, "_load_module", side_effect=_make_load_module_side_effect(2)
        ),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)
        service = BenchmarkExecutionService()
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=run_id,
            write_to_db=True,
        )

    _assert_run_completed(
        session_manager, run_id, test_ids, "get-prompts-api response"
    )

    client = TestClient(fastapi_app)
    response = client.get(f"/api/benchmark-runs/{run_id}/prompts")

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    for item in data:
        assert "id" in item
        assert "run_test_id" in item
        assert "prompt_id" in item
        assert item.get("prediction_result") is not None
        assert item.get("evaluation_prediction_result") is not None
        assert item.get("evaluation_accuracy") is not None
        assert "test_name" in item
        assert isinstance(item.get("test_name"), str)
        assert item.get("test_id") is not None


@pytest.mark.integration
def test_get_benchmark_run_results_api(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    GET /api/benchmark-runs/{run_id}/results returns run, non-empty bundles with test_ids,
    and prompts each including test_id after execute_bundle.
    """
    assert CONFIG_PATH_TWO_TESTS.exists(), f"Fixture missing: {CONFIG_PATH_TWO_TESTS}"
    shared_config_seed_service.seed_if_test_file_changed(
        config_path=CONFIG_PATH_TWO_TESTS
    )
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = sorted(config_adapter.get_test_ids_by_bundle_id(bundle_id))
    assert len(test_ids) >= 2

    session_manager = SessionManager.get_instance()
    run_id = _insert_benchmark_run(
        session_manager, "integration-get-results-api"
    )
    BenchmarkRunTestBundlePopulationService().populate_run_bundle(
        run_id, "minimal-bundle"
    )

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(
            response="get-results-api response", context=[]
        )
    )
    mock_connector.configure = MagicMock()
    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if (
            module_type == ModuleTypes.CONNECTOR
            and module_name == "mock_execute_bundle_connector"
        ):
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager, "_load_module", side_effect=_make_load_module_side_effect(2)
        ),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)
        service = BenchmarkExecutionService()
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=run_id,
            write_to_db=True,
        )

    _assert_run_completed(
        session_manager, run_id, test_ids, "get-results-api response"
    )

    client = TestClient(fastapi_app)
    response = client.get(f"/api/benchmark-runs/{run_id}/results")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["run"]["id"] == run_id
    assert isinstance(data["bundles"], list)
    assert len(data["bundles"]) >= 1
    b0 = data["bundles"][0]
    assert "test_bundle_id" in b0
    assert "name" in b0
    assert "system_name" in b0
    assert isinstance(b0["test_ids"], list)
    assert set(b0["test_ids"]) == set(test_ids)

    prompts = data["prompts"]
    assert isinstance(prompts, list)
    assert len(prompts) >= 2
    for item in prompts:
        assert item.get("test_id") is not None
        assert item["test_id"] in test_ids


@pytest.mark.integration
def test_get_benchmark_run_test_bundles_api_after_execute(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    After execute_bundle with DB + mocks, GET /api/benchmark-runs/{run_id}/run-test-bundles
    returns all benchmark_run_test_bundle rows for that run (one per test in the bundle).
    """
    assert CONFIG_PATH_TWO_TESTS.exists(), f"Fixture missing: {CONFIG_PATH_TWO_TESTS}"
    shared_config_seed_service.seed_if_test_file_changed(
        config_path=CONFIG_PATH_TWO_TESTS
    )
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = sorted(config_adapter.get_test_ids_by_bundle_id(bundle_id))
    assert len(test_ids) >= 2

    session_manager = SessionManager.get_instance()
    run_id = _insert_benchmark_run(
        session_manager, "integration-run-test-bundles-api"
    )
    BenchmarkRunTestBundlePopulationService().populate_run_bundle(
        run_id, "minimal-bundle"
    )

    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(
            response="run-test-bundles-api response", context=[]
        )
    )
    mock_connector.configure = MagicMock()
    mock_metric = MagicMock()
    mock_metric.get_individual_result = AsyncMock(return_value=1.0)
    mock_metric.get_results = AsyncMock(return_value={})
    mock_metric.update_metric_params = MagicMock()
    connector_entity = ConnectorEntity(
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_module_loader_load = ModuleLoader.load

    def mock_load_module(module_name, module_type):
        if (
            module_type == ModuleTypes.CONNECTOR
            and module_name == "mock_execute_bundle_connector"
        ):
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_module_loader_load(module_name, module_type)

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager, "_load_module", side_effect=_make_load_module_side_effect(2)
        ),
        patch.object(ModuleLoader, "load", side_effect=mock_load_module),
        patch("domain.services.task_manager.AppConfig") as mock_app_config_cls,
    ):
        mock_app_config = MagicMock()
        mock_app_config.DEFAULT_RESULTS_PATH = str(tmp_path)
        mock_app_config.get_metric_config.return_value = MagicMock(
            params={"categorise_result": False}
        )
        mock_app_config_cls.return_value = mock_app_config
        mock_app_config_cls.DEFAULT_RESULTS_PATH = str(tmp_path)
        service = BenchmarkExecutionService()
        service.execute_bundle(
            "minimal-bundle",
            "mock_execute_bundle_connector",
            run_id=run_id,
            write_to_db=True,
        )

    _assert_run_completed(
        session_manager, run_id, test_ids, "run-test-bundles-api response"
    )

    client = TestClient(fastapi_app)
    response = client.get(f"/api/benchmark-runs/{run_id}/run-test-bundles")

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(test_ids)
    returned_test_ids = sorted(row["test_id"] for row in data)
    assert returned_test_ids == test_ids
    for row in data:
        assert row["run_id"] == run_id
        assert row["test_bundle_id"] == bundle_id
        assert row["id"] is not None
        assert "test_id" in row
