"""
Integration tests for start_benchmark_run with real database.

Seeds config via seed_if_test_file_changed, then calls BenchmarkExecutionService.start_benchmark_run
with Process patched to run in-process. Asserts benchmark_run row, no combined bundle JSON file
(API path), run_test/prompts, and duplicate run name rejection.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestBundleModel,
    BenchmarkRunTestPromptModel,
    BenchmarkRunTestStatusModel,
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from application.services.benchmark_execution_service import BenchmarkExecutionService
from application.services.database_connector_config_service import (
    DatabaseConnectorConfigService,
)
from application.services.benchmark_run_service import BenchmarkRunService
from application.services.provider_seed_service import ProviderSeedService
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
from application.services.benchmark_dataset_seed_service import (
    BenchmarkDatasetSeedService,
)
from domain.services.app_config import AppConfig
from domain.services.task_manager import TaskManager
from domain.services.enums.module_types import ModuleTypes
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity

import time
import uuid

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
CONFIG_PATH = FIXTURES_DIR / "shared_minimal.yaml"
CONFIG_PATH_TWO_TESTS = FIXTURES_DIR / "shared_minimal_two_tests.yaml"
MOONSHOT_CORE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SHARED_CONFIG_PATH = MOONSHOT_CORE_ROOT / "data" / "test_configs" / "shared.yaml"

STUB_LLM_PROVIDER_ID = 1
STUB_LLM_PROVIDER_MODEL_ID = 1
STUB_LLM_PROVIDER_MODEL_CONFIG_ID = 1


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
    """Return list of (prediction_result, evaluation_prediction_result, evaluation_accuracy) per row.

    Callers assert on prediction and evaluation text; ``evaluation_accuracy`` may be NULL for some metrics.
    """
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


def _make_load_module_side_effect(num_run_benchmarks: int):
    """Build _load_module side_effect list: 2 items per run_benchmark (dataset, prompt_processor)."""
    from adapters.prompt_processor.asyncio_prompt_processor_adapter import AsyncioPromptProcessor

    return [
        MagicMock(),
        (AsyncioPromptProcessor(), "asyncio_pp"),
    ] * num_run_benchmarks


def _assert_run_completed(session_manager, run_id: int, test_ids: list, expected_prediction: str):
    """Assert all tests for run_id are completed with prediction and evaluation text (not ``evaluation_accuracy``)."""
    for test_id in test_ids:
        run_test_id, status, end_dt = _get_run_test_status(session_manager, run_id, test_id)
        assert run_test_id is not None, f"run_test_status missing for run_id={run_id}, test_id={test_id}"
        assert status == "completed"
        assert end_dt is not None
        prompts = _get_run_test_prompts(session_manager, run_test_id)
        assert len(prompts) >= 1
        for prediction_result, evaluation_prediction_result, _ in prompts:
            assert prediction_result is not None
            assert prediction_result == expected_prediction
            assert evaluation_prediction_result is not None


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
    Assert benchmark_run row exists, get_all_runs includes that run, no combined bundle JSON file,
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
        patch.object(
            DatabaseConnectorConfigService,
            "build_connector_entity",
            return_value=connector_entity,
        ),
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
            llm_provider_id=STUB_LLM_PROVIDER_ID,
            llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
            llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
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
    assert not result_file.exists(), (
        f"API-started runs should not write combined bundle JSON; unexpected file: {result_file}"
    )

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
        patch.object(
            DatabaseConnectorConfigService,
            "build_connector_entity",
            return_value=connector_entity,
        ),
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
            llm_provider_id=STUB_LLM_PROVIDER_ID,
            llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
            llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
        )
        service.start_benchmark_run(
            run_name=run_name_2,
            bundle_names=["minimal-bundle"],
            llm_provider_id=STUB_LLM_PROVIDER_ID,
            llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
            llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
        )

    run_entity_1 = BenchmarkRunService().get_run_by_name(run_name_1)
    run_entity_2 = BenchmarkRunService().get_run_by_name(run_name_2)
    assert run_entity_1 is not None and run_entity_1.id is not None
    assert run_entity_2 is not None and run_entity_2.id is not None
    assert run_entity_1.id != run_entity_2.id

    result_file = tmp_path / "minimal-bundle.json"
    assert not result_file.exists(), (
        f"API-started runs should not write combined bundle JSON; unexpected file: {result_file}"
    )

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
        patch.object(
            DatabaseConnectorConfigService,
            "build_connector_entity",
            return_value=connector_entity,
        ),
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
            llm_provider_id=STUB_LLM_PROVIDER_ID,
            llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
            llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
        )
        with pytest.raises(IntegrityError):
            service.start_benchmark_run(
                run_name=run_name,
                bundle_names=["minimal-bundle"],
                llm_provider_id=STUB_LLM_PROVIDER_ID,
                llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
                llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
            )


@pytest.mark.integration
def test_start_benchmark_run_test_bundle(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Seed DB from data/test_configs/shared.yaml, then run start_benchmark_run with
    the test-bundle bundle. Process is patched to run in-process; connector and
    llamaguardannotator_adapter are mocked. Asserts benchmark_run row, no combined bundle JSON file,
    and completed run_test/prompts.
    """
    assert SHARED_CONFIG_PATH.exists(), f"Shared config missing: {SHARED_CONFIG_PATH}"
    shared_config_seed_service.seed_if_test_file_changed(config_path=SHARED_CONFIG_PATH)

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("test-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= 1

    run_name = "start-benchmark-run-test-bundle-integration"
    expected_prediction = "test_bundle integration response"

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
        if module_type == ModuleTypes.METRIC and module_name in (
            "llamaguardannotator_adapter",
            "accuracy_adapter",
            "refusal_adapter",
        ):
            return (mock_metric, module_name)
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
        patch.object(
            DatabaseConnectorConfigService,
            "build_connector_entity",
            return_value=connector_entity,
        ),
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
            bundle_names=["test-bundle"],
            llm_provider_id=STUB_LLM_PROVIDER_ID,
            llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
            llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
        )

    run_entity = BenchmarkRunService().get_run_by_name(run_name)
    assert run_entity is not None, f"Expected benchmark_run row with name {run_name}"
    assert run_entity.id is not None
    assert run_entity.status == "completed"
    assert run_entity.end_time is not None

    result_file = tmp_path / "test-bundle.json"
    assert not result_file.exists(), (
        f"API-started runs should not write combined bundle JSON; unexpected file: {result_file}"
    )

    session_manager = SessionManager.get_instance()
    _assert_run_completed(session_manager, run_entity.id, test_ids, expected_prediction)
    _assert_all_statuses_completed(session_manager, run_entity.id)


@pytest.mark.integration
def test_start_benchmark_run_tests_by_bundle_subset_one_of_two(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Seed minimal-bundle with two tests, run start_benchmark_run with tests_by_bundle selecting
    only one benchmark_test.id; assert run completes, one run_test_bundle row, no status for omitted test.
    """
    assert CONFIG_PATH_TWO_TESTS.exists(), f"Fixture config missing: {CONFIG_PATH_TWO_TESTS}"
    BenchmarkDatasetSeedService(
        source_dataset_repository=FileDatasetRepository(),
        target_dataset_repository=SqlAlchemyDatasetRepository(),
    ).seed_benchmark_dataset("test_sample_dataset")
    # Use a fresh bundle version so this test always sees two tests (session DB may already have v1 minimal-bundle).
    shared_config_seed_service.seed_from_config(config_path=CONFIG_PATH_TWO_TESTS, version=10)

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    all_test_ids = sorted(config_adapter.get_test_ids_by_bundle_id(bundle_id))
    assert len(all_test_ids) == 2
    chosen = [all_test_ids[0]]
    omitted = all_test_ids[1]

    run_name = f"subset-benchmark-run-{uuid.uuid4().hex[:12]}"
    expected_prediction = "subset start_benchmark_run response"

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
        patch.object(
            DatabaseConnectorConfigService,
            "build_connector_entity",
            return_value=connector_entity,
        ),
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
            llm_provider_id=STUB_LLM_PROVIDER_ID,
            llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
            llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
            tests_by_bundle={"minimal-bundle": chosen},
        )

    run_entity = BenchmarkRunService().get_run_by_name(run_name)
    assert run_entity is not None
    assert run_entity.id is not None
    assert run_entity.status == "completed"

    session_manager = SessionManager.get_instance()
    _assert_run_completed(session_manager, run_entity.id, chosen, expected_prediction)
    _assert_all_statuses_completed(session_manager, run_entity.id)
    omitted_rtid, _, _ = _get_run_test_status(session_manager, run_entity.id, omitted)
    assert omitted_rtid is None

    with session_manager.get_session() as session:
        n_rtb = (
            session.query(BenchmarkRunTestBundleModel)
            .filter(BenchmarkRunTestBundleModel.run_id == run_entity.id)
            .count()
        )
        assert n_rtb == 1


@pytest.mark.integration
def test_start_benchmark_run_continues_after_one_test_fails(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    With continue_on_test_failure=True (API path), a failing test must not stop sibling tests.
    """
    assert CONFIG_PATH_TWO_TESTS.exists(), f"Fixture config missing: {CONFIG_PATH_TWO_TESTS}"
    BenchmarkDatasetSeedService(
        source_dataset_repository=FileDatasetRepository(),
        target_dataset_repository=SqlAlchemyDatasetRepository(),
    ).seed_benchmark_dataset("test_sample_dataset")
    shared_config_seed_service.seed_from_config(config_path=CONFIG_PATH_TWO_TESTS, version=12)

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = sorted(config_adapter.get_test_ids_by_bundle_id(bundle_id))
    assert len(test_ids) == 2
    first_test_id, second_test_id = test_ids[0], test_ids[1]

    run_name = f"continue-on-fail-run-{uuid.uuid4().hex[:12]}"
    expected_prediction = "continue on fail response"

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
    real_run_benchmark = TaskManager.run_benchmark
    run_benchmark_calls = {"n": 0}

    async def run_benchmark_fail_first(self, *args, **kwargs):
        run_benchmark_calls["n"] += 1
        if run_benchmark_calls["n"] == 1:
            raise RuntimeError("simulated first test failure")
        return await real_run_benchmark(self, *args, **kwargs)

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
        patch.object(
            DatabaseConnectorConfigService,
            "build_connector_entity",
            return_value=connector_entity,
        ),
        patch.object(TaskManager, "run_benchmark", run_benchmark_fail_first),
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
            run_name=run_name,
            bundle_names=["minimal-bundle"],
            llm_provider_id=STUB_LLM_PROVIDER_ID,
            llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
            llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
            continue_on_test_failure=True,
        )

    assert run_benchmark_calls["n"] == 2, "Both tests must be attempted"

    run_entity = BenchmarkRunService().get_run_by_name(run_name)
    assert run_entity is not None
    assert run_entity.id is not None
    assert run_entity.status == "completed"
    assert run_entity.end_time is not None

    session_manager = SessionManager.get_instance()
    _, first_status, first_end_dt = _get_run_test_status(
        session_manager, run_entity.id, first_test_id
    )
    assert first_status == "failed"
    assert first_end_dt is not None

    second_run_test_id, second_status, second_end_dt = _get_run_test_status(
        session_manager, run_entity.id, second_test_id
    )
    assert second_status == "completed"
    assert second_end_dt is not None
    prompts = _get_run_test_prompts(session_manager, second_run_test_id)
    assert len(prompts) >= 1
    for prediction_result, evaluation_prediction_result, _ in prompts:
        assert prediction_result == expected_prediction
        assert evaluation_prediction_result is not None


@pytest.mark.integration
def test_start_benchmark_run_prompts_by_test_limits_prompt_count(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    start_benchmark_run with prompts_by_test populates only the first N prompts per test.
    """
    assert CONFIG_PATH_TWO_TESTS.exists(), f"Fixture config missing: {CONFIG_PATH_TWO_TESTS}"
    BenchmarkDatasetSeedService(
        source_dataset_repository=FileDatasetRepository(),
        target_dataset_repository=SqlAlchemyDatasetRepository(),
    ).seed_benchmark_dataset("test_sample_dataset")
    shared_config_seed_service.seed_from_config(config_path=CONFIG_PATH_TWO_TESTS, version=11)

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    all_test_ids = sorted(config_adapter.get_test_ids_by_bundle_id(bundle_id))
    assert len(all_test_ids) == 2
    test_id_1, test_id_2 = all_test_ids

    run_name = f"prompts-by-test-run-{uuid.uuid4().hex[:12]}"
    expected_prediction = "prompts_by_test integration response"

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
        patch.object(
            DatabaseConnectorConfigService,
            "build_connector_entity",
            return_value=connector_entity,
        ),
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
            run_name=run_name,
            bundle_names=["minimal-bundle"],
            llm_provider_id=STUB_LLM_PROVIDER_ID,
            llm_provider_model_id=STUB_LLM_PROVIDER_MODEL_ID,
            llm_provider_model_config_id=STUB_LLM_PROVIDER_MODEL_CONFIG_ID,
            prompts_by_test={test_id_1: 2, test_id_2: 1},
        )

    run_entity = BenchmarkRunService().get_run_by_name(run_name)
    assert run_entity is not None
    assert run_entity.id is not None
    assert run_entity.status == "completed"

    session_manager = SessionManager.get_instance()
    _assert_run_completed(
        session_manager, run_entity.id, all_test_ids, expected_prediction
    )
    _assert_all_statuses_completed(session_manager, run_entity.id)

    run_test_id_1, _, _ = _get_run_test_status(session_manager, run_entity.id, test_id_1)
    run_test_id_2, _, _ = _get_run_test_status(session_manager, run_entity.id, test_id_2)
    assert run_test_id_1 is not None
    assert run_test_id_2 is not None
    assert len(_get_run_test_prompts(session_manager, run_test_id_1)) == 2
    assert len(_get_run_test_prompts(session_manager, run_test_id_2)) == 1


def _ensure_openai_benchmark_ids() -> tuple[int, int, int]:
    ProviderSeedService().seed_hardcoded_providers()
    session_manager = SessionManager.get_instance()
    with session_manager.get_session() as session:
        provider = (
            session.query(LLMProviderModel)
            .filter(LLMProviderModel.system_name == "openai_adapter")
            .order_by(LLMProviderModel.id.desc())
            .first()
        )
        assert provider is not None
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
                name="pytest-live-openai-default",
            )
            session.add(cfg)
            session.flush()
        session.commit()
        return int(provider.id), int(model.id), int(cfg.id)


def _poll_benchmark_run_completed(run_name: str, timeout_s: float = 300.0, interval_s: float = 0.5):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        run_entity = BenchmarkRunService().get_run_by_name(run_name)
        if run_entity is not None and run_entity.status == "completed":
            return run_entity
        if run_entity is not None and run_entity.status not in ("running", "completed"):
            pytest.fail(f"benchmark_run ended unexpectedly: status={run_entity.status!r}")
        time.sleep(interval_s)
    pytest.fail(f"benchmark_run {run_name!r} not completed within {timeout_s}s")


def _assert_predictions_from_real_model(session_manager, run_id: int, test_ids: list[int]):
    for test_id in test_ids:
        run_test_id, status, end_dt = _get_run_test_status(session_manager, run_id, test_id)
        assert run_test_id is not None
        assert status == "completed"
        assert end_dt is not None
        prompts = _get_run_test_prompts(session_manager, run_test_id)
        assert len(prompts) >= 1
        for prediction_result, evaluation_prediction_result, _ in prompts:
            assert prediction_result and prediction_result.strip()
            assert evaluation_prediction_result is not None
            assert evaluation_prediction_result.strip()


@pytest.mark.live_openai
@pytest.mark.skipif(
    not (os.getenv("OPENAI_API_KEY") or "").strip(),
    reason="OPENAI_API_KEY not set (live OpenAI test skipped)",
)
def test_start_benchmark_run_live_openai_real_api(
    shared_config_seed_service,
    test_db_env,
    tmp_path,
):
    """
    Live OpenAI: real ``multiprocessing.Process``, ``BenchmarkExecutionService.start_benchmark_run``,
    real ``openai_adapter`` and ``AsyncOpenAI.chat.completions.create`` (benchmark + refusal metric).

    Preconditions:
    - ``OPENAI_API_KEY`` in the environment (parent and worker inherit env).
    - Session-scoped SQLite via ``MOONSHOT_DB_PATH`` (``test_db_env``); migrations applied by seed flow.
    - Relational ids from seeded ``llm_provider`` / model / ``model_config`` (``openai_adapter`` + ``gpt-4o-mini``),
      not hard-coded stub ids.
    - Bundle ``minimal-bundle`` from ``fixtures/shared_minimal.yaml`` (``refusal_adapter``).

    Opt-in: default pytest excludes ``live_openai`` (see ``pytest.ini`` ``addopts``). Run explicitly, e.g.:
    ``cd moonshot_core && pytest -o addopts= -m live_openai tests/application/services/test_start_benchmark_run_integration.py::test_start_benchmark_run_live_openai_real_api``

    Asserts run reaches ``completed``, no combined bundle JSON under ``tmp_path`` (API path skips file),
    and prompt rows have non-empty ``prediction_result`` and non-empty ``evaluation_prediction_result``.
    Does not require ``evaluation_accuracy`` (nullable for dict-shaped metric results). Uses ``moonshot_config.yaml`` via ``MS_CONFIG_PATH``.
    """
    assert CONFIG_PATH.exists(), f"Fixture config missing: {CONFIG_PATH}"
    shared_config_seed_service.seed_if_test_file_changed(config_path=CONFIG_PATH)

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_db_id = config_adapter.get_bundle_id_by_system_name_latest("minimal-bundle")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_db_id)
    assert len(test_ids) >= 1

    llm_provider_id, llm_provider_model_id, llm_provider_model_config_id = _ensure_openai_benchmark_ids()

    run_name = f"live-openai-{uuid.uuid4().hex[:12]}"
    old_results = os.environ.get("MOONSHOT_BENCHMARK_RESULTS_DIR")
    old_ms_config = os.environ.get("MS_CONFIG_PATH")
    os.environ["MOONSHOT_BENCHMARK_RESULTS_DIR"] = str(tmp_path)
    os.environ["MS_CONFIG_PATH"] = str(MOONSHOT_CORE_ROOT / "moonshot_config.yaml")
    try:
        BenchmarkExecutionService().start_benchmark_run(
            run_name=run_name,
            bundle_names=["minimal-bundle"],
            llm_provider_id=llm_provider_id,
            llm_provider_model_id=llm_provider_model_id,
            llm_provider_model_config_id=llm_provider_model_config_id,
        )
        run_entity = _poll_benchmark_run_completed(run_name)
        assert run_entity.id is not None
        assert run_entity.end_time is not None

        result_file = tmp_path / "minimal-bundle.json"
        assert not result_file.exists(), (
            f"API-started runs should not write combined bundle JSON; unexpected file: {result_file}"
        )

        session_manager = SessionManager.get_instance()
        _assert_predictions_from_real_model(session_manager, run_entity.id, test_ids)
        _assert_all_statuses_completed(session_manager, run_entity.id)
    finally:
        if old_results is None:
            os.environ.pop("MOONSHOT_BENCHMARK_RESULTS_DIR", None)
        else:
            os.environ["MOONSHOT_BENCHMARK_RESULTS_DIR"] = old_results
        if old_ms_config is None:
            os.environ.pop("MS_CONFIG_PATH", None)
        else:
            os.environ["MS_CONFIG_PATH"] = old_ms_config
