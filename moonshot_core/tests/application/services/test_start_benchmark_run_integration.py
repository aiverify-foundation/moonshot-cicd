"""
Integration tests for start_benchmark_run with real database.

Seeds config via seed_if_test_file_changed, then calls BenchmarkExecutionService.start_benchmark_run
with Process patched to run in-process. Asserts benchmark_run row, result file, run_test/prompts,
and duplicate run name rejection.
"""

import os
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestPromptModel,
    BenchmarkRunTestStatusModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from application.services.benchmark_execution_service import BenchmarkExecutionService
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


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
CONFIG_PATH = FIXTURES_DIR / "shared_minimal.yaml"
MOONSHOT_CORE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SHARED_CONFIG_PATH = MOONSHOT_CORE_ROOT / "data" / "test_configs" / "shared.yaml"


@pytest.fixture(scope="session")
def test_db_path():
    """Shared database path for this module; cleared once at session start."""
    moonshot_core_root = Path(__file__).resolve().parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_start_benchmark_run.db"
    if db_path.exists():
        db_path.unlink()
    return str(db_path)


@pytest.fixture(scope="session")
def test_db_env(test_db_path):
    """Set MOONSHOT_DB_PATH and reset SessionManager (session-scoped)."""
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


def _assert_all_statuses_completed(session_manager, run_id: int):
    """Assert all benchmark_run_test_status and benchmark_run_test_prompt rows for run_id are completed."""
    with session_manager.get_session() as session:
        run_test_statuses = (
            session.query(BenchmarkRunTestStatusModel)
            .filter(BenchmarkRunTestStatusModel.run_id == run_id)
            .all()
        )
        assert len(run_test_statuses) >= 1, f"No run_test_status rows for run_id={run_id}"
        for rts in run_test_statuses:
            assert rts.status == "completed", (
                f"run_test_status id={rts.id} (run_id={run_id}, test_id={rts.test_id}) "
                f"expected status 'completed', got {rts.status!r}"
            )
            assert rts.end_dt is not None, (
                f"run_test_status id={rts.id} (run_id={run_id}) expected end_dt set"
            )
        run_test_ids = [rts.id for rts in run_test_statuses]
        for run_test_id in run_test_ids:
            prompts = (
                session.query(BenchmarkRunTestPromptModel)
                .filter(BenchmarkRunTestPromptModel.run_test_id == run_test_id)
                .all()
            )
            for prompt in prompts:
                assert prompt.status == "completed", (
                    f"benchmark_run_test_prompt id={prompt.id} (run_test_id={run_test_id}) "
                    f"expected status 'completed', got {prompt.status!r}"
                )


@pytest.mark.integration
def test_start_benchmark_run_happy_path_with_db(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Seed DB via seed_if_test_file_changed, then run start_benchmark_run with one bundle.
    Process is patched to run the bundle in the current process; connector/metric mocked.
    Assert benchmark_run row exists, get_all_runs includes that run, result file is written,
    and run_test/prompts completed.
    """
    assert CONFIG_PATH.exists(), f"Fixture config missing: {CONFIG_PATH}"

    shared_config_seed_service.seed_if_test_file_changed(config_path=CONFIG_PATH)

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 1

    run_name = "start-benchmark-run-integration-run"
    expected_prediction = "start_benchmark_run integration test response"

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
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_load = ModuleLoader.load

    def mock_load_module_impl(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_execute_bundle_connector":
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_load(module_name, module_type)

    def fake_process(*, target=None, args=(), **kwargs):
        fake = MagicMock()
        def start():
            if target is not None:
                target(*args)
        fake.start = start
        return fake

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager,
            "_load_module",
            side_effect=_make_load_module_side_effect(1),
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

        service = BenchmarkExecutionService()
        service.start_benchmark_run(
            run_name=run_name,
            bundle_names=["minimal-bundle"],
            llm_provider_name="TestProvider",
            llm_provider_config_name="mock_execute_bundle_connector",
        )

    run_entity = BenchmarkRunService().get_run_by_name(run_name)
    assert run_entity is not None, f"Expected benchmark_run row with name {run_name}"
    run_id = run_entity.id
    assert run_id is not None
    assert run_entity.status == "completed"
    assert run_entity.end_time is not None

    all_runs = BenchmarkRunService().get_all_runs()
    matching = [r for r in all_runs if r.id == run_id]
    assert len(matching) == 1, f"Expected exactly one benchmark_run with id={run_id} in get_all_runs()"
    assert matching[0].name == run_name
    assert matching[0].status == "completed"

    result_file = tmp_path / "minimal-bundle.json"
    assert result_file.exists(), f"Expected result file at {result_file}"
    data = json.loads(result_file.read_text())
    assert "run_metadata" in data
    assert "run_results" in data
    assert len(data["run_results"]) >= 1

    session_manager = SessionManager.get_instance()
    _assert_run_completed(session_manager, run_id, test_ids, expected_prediction)


@pytest.mark.integration
def test_start_benchmark_run_two_runs_back_to_back(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Call start_benchmark_run twice with two different run names; assert both runs
    exist and both have completed run_test_status and prompt results.
    """
    assert CONFIG_PATH.exists(), f"Fixture config missing: {CONFIG_PATH}"
    shared_config_seed_service.seed_if_test_file_changed(config_path=CONFIG_PATH)

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 1

    run_name_1 = "start-benchmark-run-two-runs-1"
    run_name_2 = "start-benchmark-run-two-runs-2"
    expected_prediction = "two start_benchmark_runs response"

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
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_load = ModuleLoader.load

    def mock_load_module_impl(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_execute_bundle_connector":
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_load(module_name, module_type)

    def fake_process(*, target=None, args=(), **kwargs):
        fake = MagicMock()
        def start():
            if target is not None:
                target(*args)
        fake.start = start
        return fake

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager,
            "_load_module",
            side_effect=_make_load_module_side_effect(2),
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

        service = BenchmarkExecutionService()
        service.start_benchmark_run(
            run_name=run_name_1,
            bundle_names=["minimal-bundle"],
            llm_provider_name="TestProvider",
            llm_provider_config_name="mock_execute_bundle_connector",
        )
        service.start_benchmark_run(
            run_name=run_name_2,
            bundle_names=["minimal-bundle"],
            llm_provider_name="TestProvider",
            llm_provider_config_name="mock_execute_bundle_connector",
        )

    run_entity_1 = BenchmarkRunService().get_run_by_name(run_name_1)
    run_entity_2 = BenchmarkRunService().get_run_by_name(run_name_2)
    assert run_entity_1 is not None and run_entity_1.id is not None
    assert run_entity_2 is not None and run_entity_2.id is not None
    assert run_entity_1.id != run_entity_2.id

    result_file = tmp_path / "minimal-bundle.json"
    assert result_file.exists(), f"Expected result file at {result_file}"
    data = json.loads(result_file.read_text())
    assert "run_metadata" in data and "run_results" in data

    session_manager = SessionManager.get_instance()
    _assert_run_completed(session_manager, run_entity_1.id, test_ids, expected_prediction)
    _assert_run_completed(session_manager, run_entity_2.id, test_ids, expected_prediction)


@pytest.mark.integration
def test_start_benchmark_run_duplicate_name_raises(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    start_benchmark_run with a run name that already exists must not run (DB unique on name).
    Second call should raise IntegrityError from save_run.
    """
    assert CONFIG_PATH.exists(), f"Fixture config missing: {CONFIG_PATH}"
    shared_config_seed_service.seed_if_test_file_changed(config_path=CONFIG_PATH)

    run_name = "start-benchmark-run-dup-name"
    mock_connector = MagicMock()
    mock_connector.get_response = AsyncMock(
        return_value=ConnectorResponseEntity(response="dup test response", context=[])
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

    real_load = ModuleLoader.load

    def mock_load_module_impl(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_execute_bundle_connector":
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_load(module_name, module_type)

    def fake_process(*, target=None, args=(), **kwargs):
        fake = MagicMock()
        def start():
            if target is not None:
                target(*args)
        fake.start = start
        return fake

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager,
            "_load_module",
            side_effect=_make_load_module_side_effect(1),
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

        service = BenchmarkExecutionService()
        service.start_benchmark_run(
            run_name=run_name,
            bundle_names=["minimal-bundle"],
            llm_provider_name="TestProvider",
            llm_provider_config_name="mock_execute_bundle_connector",
        )
        with pytest.raises(IntegrityError):
            service.start_benchmark_run(
                run_name=run_name,
                bundle_names=["minimal-bundle"],
                llm_provider_name="TestProvider",
                llm_provider_config_name="mock_execute_bundle_connector",
            )


@pytest.mark.integration
def test_start_benchmark_run_test_prompts_bundle(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Seed DB from data/test_configs/shared.yaml, then run start_benchmark_run with
    the test-prompts bundle. Process is patched to run in-process; connector and
    accuracy_adapter are mocked. Asserts benchmark_run row, result file
    test-prompts.json, and completed run_test/prompts.
    """
    assert SHARED_CONFIG_PATH.exists(), f"Shared config missing: {SHARED_CONFIG_PATH}"
    shared_config_seed_service.seed_if_test_file_changed(config_path=SHARED_CONFIG_PATH)

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("test-prompts")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 1

    run_name = "start-benchmark-run-test-prompts-integration"
    expected_prediction = "test_prompts integration response"

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
        connector_adapter="mock_execute_bundle_connector",
        model="test-model",
        model_endpoint="",
        params={"max_concurrency": 2},
    )

    from domain.services.loader.module_loader import ModuleLoader

    real_load = ModuleLoader.load

    def mock_load_module_impl(module_name, module_type):
        if module_type == ModuleTypes.CONNECTOR and module_name == "mock_execute_bundle_connector":
            return (mock_connector, None)
        if module_type == ModuleTypes.METRIC and module_name == "accuracy_adapter":
            return (mock_metric, "accuracy_adapter")
        if module_type == ModuleTypes.METRIC and module_name == "refusal_adapter":
            return (mock_metric, "refusal_adapter")
        return real_load(module_name, module_type)

    def fake_process(*, target=None, args=(), **kwargs):
        fake = MagicMock()
        def start():
            if target is not None:
                target(*args)
        fake.start = start
        return fake

    with (
        patch.object(AppConfig, "DEFAULT_RESULTS_PATH", str(tmp_path)),
        patch.object(TaskManager, "_get_connector_config", return_value=connector_entity),
        patch.object(
            TaskManager,
            "_load_module",
            side_effect=_make_load_module_side_effect(1),
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

        service = BenchmarkExecutionService()
        service.start_benchmark_run(
            run_name=run_name,
            bundle_names=["test-prompts"],
            llm_provider_name="TestProvider",
            llm_provider_config_name="mock_execute_bundle_connector",
        )

    run_entity = BenchmarkRunService().get_run_by_name(run_name)
    assert run_entity is not None, f"Expected benchmark_run row with name {run_name}"
    assert run_entity.id is not None
    assert run_entity.status == "completed"
    assert run_entity.end_time is not None

    result_file = tmp_path / "test-prompts.json"
    assert result_file.exists(), f"Expected result file at {result_file}"
    data = json.loads(result_file.read_text())
    assert "run_metadata" in data
    assert "run_results" in data
    assert len(data["run_results"]) >= 1

    session_manager = SessionManager.get_instance()
    _assert_run_completed(session_manager, run_entity.id, test_ids, expected_prediction)
    _assert_all_statuses_completed(session_manager, run_entity.id)
