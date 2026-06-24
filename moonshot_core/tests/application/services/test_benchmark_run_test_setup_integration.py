"""
Integration tests for BenchmarkRunTestSetupService.create_run_test_with_prompts.

Uses a real database: seed from shared config, create benchmark run(s), then exercise
create_run_test_with_prompts. Three tests: happy path, idempotency, two happy paths.
"""

from pathlib import Path
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestStatusModel,
    BenchmarkRunTestPromptModel,
    BenchmarkTestDatasetPromptModel,
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


@pytest.fixture(scope="function")
def test_db_path():
    """Temporary database path for integration tests."""
    moonshot_core_root = Path(__file__).resolve().parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_setup.db"
    if db_path.exists():
        db_path.unlink()
    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set MOONSHOT_DB_PATH and reset SessionManager so migrations run on first use."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def config_path_two_tests():
    """Path to shared config with minimal-bundle and two tests."""
    return (
        Path(__file__).resolve().parent
        / "fixtures"
        / "shared_minimal_two_tests.yaml"
    )


@pytest.fixture
def shared_config_seed_service(test_db_env):
    """Build SharedConfigSeedService with full stack for seeding."""
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


def _count_run_test_status_by_run_id(session_manager, run_id: int) -> int:
    """Return number of benchmark_run_test_status rows for the given run_id."""
    with session_manager.get_session() as session:
        return (
            session.query(BenchmarkRunTestStatusModel)
            .filter(BenchmarkRunTestStatusModel.run_id == run_id)
            .count()
        )


def _count_run_test_prompts_by_run_test_id(
    session_manager, run_test_id: int
) -> int:
    """Return number of benchmark_run_test_prompt rows for the given run_test_id."""
    with session_manager.get_session() as session:
        return (
            session.query(BenchmarkRunTestPromptModel)
            .filter(BenchmarkRunTestPromptModel.run_test_id == run_test_id)
            .count()
        )


def _seed_and_get_run_and_test_ids(
    shared_config_seed_service,
    config_path: Path,
    session_manager,
    run_name: str,
    min_tests: int = 1,
):
    """Seed from config, insert one run, return (run_id, test_ids list)."""
    result = shared_config_seed_service.seed_if_test_file_changed(
        config_path=config_path
    )
    assert result is True
    config_adapter = BenchmarkTestConfigAdapter()
    bundle_id = config_adapter.get_bundle_id_by_system_name_latest(
        "minimal-bundle"
    )
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_id)
    assert len(test_ids) >= min_tests
    run_id = _insert_benchmark_run(session_manager, run_name)
    assert run_id is not None
    return run_id, test_ids


@pytest.mark.integration
class TestBenchmarkRunTestSetupIntegration:
    """Integration tests for create_run_test_with_prompts with real DB."""

    def test_happy_path(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path_two_tests,
    ):
        """Single create_run_test_with_prompts creates one status and N prompts."""
        assert config_path_two_tests.exists()
        session_manager = SessionManager.get_instance()
        run_id, test_ids = _seed_and_get_run_and_test_ids(
            shared_config_seed_service,
            config_path_two_tests,
            session_manager,
            "integration-setup-happy-path",
            min_tests=1,
        )
        test_id = test_ids[0]
        assert _count_run_test_status_by_run_id(session_manager, run_id) == 0

        setup_service = BenchmarkRunTestSetupService()
        status, prompts = setup_service.create_run_test_with_prompts(
            run_id, test_id
        )

        assert status.id is not None
        assert status.run_id == run_id
        assert status.test_id == test_id
        assert status.status == "not_started"
        assert len(prompts) >= 1
        assert _count_run_test_status_by_run_id(session_manager, run_id) == 1
        assert _count_run_test_prompts_by_run_test_id(
            session_manager, status.id
        ) == len(prompts)

    def test_idempotency(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path_two_tests,
    ):
        """Second create_run_test_with_prompts for same (run_id, test_id) returns existing; no new rows."""
        assert config_path_two_tests.exists()
        session_manager = SessionManager.get_instance()
        run_id, test_ids = _seed_and_get_run_and_test_ids(
            shared_config_seed_service,
            config_path_two_tests,
            session_manager,
            "integration-setup-idempotency",
            min_tests=1,
        )
        test_id = test_ids[0]
        setup_service = BenchmarkRunTestSetupService()

        status_1, prompts_1 = setup_service.create_run_test_with_prompts(
            run_id, test_id
        )
        run_test_id = status_1.id
        prompt_count = _count_run_test_prompts_by_run_test_id(
            session_manager, run_test_id
        )
        assert _count_run_test_status_by_run_id(session_manager, run_id) == 1

        status_2, prompts_2 = setup_service.create_run_test_with_prompts(
            run_id, test_id
        )

        assert status_2.id == status_1.id
        assert status_2.run_id == run_id
        assert status_2.test_id == test_id
        assert len(prompts_2) == len(prompts_1)
        assert _count_run_test_status_by_run_id(session_manager, run_id) == 1
        assert _count_run_test_prompts_by_run_test_id(
            session_manager, run_test_id
        ) == prompt_count

    def test_two_happy_paths(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path_two_tests,
    ):
        """Two create_run_test_with_prompts for (run_id, test_id_1) and (run_id, test_id_2) both succeed."""
        assert config_path_two_tests.exists()
        session_manager = SessionManager.get_instance()
        run_id, test_ids = _seed_and_get_run_and_test_ids(
            shared_config_seed_service,
            config_path_two_tests,
            session_manager,
            "integration-setup-two-paths",
            min_tests=2,
        )
        test_id_1, test_id_2 = test_ids[0], test_ids[1]
        assert _count_run_test_status_by_run_id(session_manager, run_id) == 0

        setup_service = BenchmarkRunTestSetupService()

        status_1, prompts_1 = setup_service.create_run_test_with_prompts(
            run_id, test_id_1
        )
        assert status_1.id is not None
        assert status_1.run_id == run_id
        assert status_1.test_id == test_id_1
        assert status_1.status == "not_started"
        assert len(prompts_1) >= 1
        assert _count_run_test_status_by_run_id(session_manager, run_id) == 1

        status_2, prompts_2 = setup_service.create_run_test_with_prompts(
            run_id, test_id_2
        )
        assert status_2.id is not None
        assert status_2.run_id == run_id
        assert status_2.test_id == test_id_2
        assert status_2.status == "not_started"
        assert status_2.id != status_1.id
        assert len(prompts_2) >= 1
        assert _count_run_test_status_by_run_id(session_manager, run_id) == 2
        assert _count_run_test_prompts_by_run_test_id(
            session_manager, status_1.id
        ) == len(prompts_1)
        assert _count_run_test_prompts_by_run_test_id(
            session_manager, status_2.id
        ) == len(prompts_2)

    def test_max_prompts_limits_to_first_n_in_dataset_order(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path_two_tests,
    ):
        """max_prompts inserts only the first N dataset prompts by benchmark_test_dataset_prompt.id."""
        assert config_path_two_tests.exists()
        session_manager = SessionManager.get_instance()
        run_id, test_ids = _seed_and_get_run_and_test_ids(
            shared_config_seed_service,
            config_path_two_tests,
            session_manager,
            "integration-setup-max-prompts",
            min_tests=1,
        )
        test_id = test_ids[0]
        config_adapter = BenchmarkTestConfigAdapter()
        dataset_id = config_adapter.get_test_dataset_id(test_id)
        with session_manager.get_session() as session:
            dataset_rows = (
                session.query(BenchmarkTestDatasetPromptModel)
                .filter(
                    BenchmarkTestDatasetPromptModel.benchmark_test_dataset_id
                    == dataset_id
                )
                .order_by(BenchmarkTestDatasetPromptModel.id)
                .all()
            )
            assert len(dataset_rows) >= 2
            expected_prompt_ids = [row.id for row in dataset_rows[:2]]

        setup_service = BenchmarkRunTestSetupService()
        status, prompts = setup_service.create_run_test_with_prompts(
            run_id, test_id, max_prompts=2
        )

        assert len(prompts) == 2
        assert [p.prompt_id for p in prompts] == expected_prompt_ids
        with session_manager.get_session() as session:
            run_prompt_rows = (
                session.query(BenchmarkRunTestPromptModel)
                .filter(BenchmarkRunTestPromptModel.run_test_id == status.id)
                .order_by(BenchmarkRunTestPromptModel.id)
                .all()
            )
            assert len(run_prompt_rows) == 2
            assert [r.prompt_id for r in run_prompt_rows] == expected_prompt_ids
