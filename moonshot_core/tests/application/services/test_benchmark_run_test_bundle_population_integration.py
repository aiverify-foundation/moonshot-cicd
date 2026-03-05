"""
Integration tests for BenchmarkRunTestBundlePopulationService.populate_run_bundle.

Uses a real database and real seeded data: SharedConfigSeedService seeds
benchmark_test_bundle, benchmark_test, and benchmark_test_bundle_grouping from
shared_minimal.yaml; then we create a benchmark run and call populate_run_bundle.
Asserts that benchmark_run_test_bundle rows are created correctly. No mocks for
DB or population service.
"""

from pathlib import Path
from datetime import datetime, timezone

import pytest
import yaml
from sqlalchemy import text

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestBundleModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.shared_config_seed_service import SharedConfigSeedService
from application.services.file_shared_config_repository import (
    FileSharedConfigRepository,
)
from application.services.file_dataset_repository import FileDatasetRepository
from application.services.benchmark_dataset_seed_service import (
    BenchmarkDatasetSeedService,
)
from application.services.benchmark_run_test_bundle_population_service import (
    BenchmarkRunTestBundlePopulationService,
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
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest.db"
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
def config_path():
    """Path to minimal shared config (bundle key minimal-bundle, one test)."""
    return (
        Path(__file__).resolve().parent
        / "fixtures"
        / "shared_minimal.yaml"
    )


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


def _count_run_test_bundle_by_run_id(session_manager, run_id: int) -> int:
    """Return number of benchmark_run_test_bundle rows for the given run_id."""
    with session_manager.get_session() as session:
        return (
            session.query(BenchmarkRunTestBundleModel)
            .filter(BenchmarkRunTestBundleModel.run_id == run_id)
            .count()
        )


def _get_run_test_bundle_rows(session_manager, run_id: int):
    """Return list of (test_bundle_id, test_id) for the given run_id."""
    with session_manager.get_session() as session:
        rows = (
            session.query(
                BenchmarkRunTestBundleModel.test_bundle_id,
                BenchmarkRunTestBundleModel.test_id,
            )
            .filter(BenchmarkRunTestBundleModel.run_id == run_id)
            .all()
        )
        return [(r[0], r[1]) for r in rows]


def _count_tests_in_config_for_bundle(config: dict, bundle_key: str) -> int:
    """Return number of tests defined for the bundle in the config."""
    bundle_data = config.get(bundle_key)
    if not isinstance(bundle_data, dict):
        return 0
    tests = bundle_data.get("tests") or []
    return len([t for t in tests if isinstance(t, dict)])


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


@pytest.mark.integration
class TestBenchmarkRunTestBundlePopulationIntegration:
    """Integration tests for populate_run_bundle with real DB and seeded data."""

    def test_populate_run_bundle_creates_expected_rows(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """
        Seed DB from shared_minimal.yaml, create a run, call populate_run_bundle;
        assert benchmark_run_test_bundle has one row per test in the bundle.
        """
        assert config_path.exists(), "Minimal fixture YAML must exist"
        session_manager = SessionManager.get_instance()

        # Seed datasets, bundle, tests, groupings (bundle system_name = "minimal-bundle")
        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result is True

        config = yaml.safe_load(config_path.read_text())
        bundle_system_name = "minimal-bundle"
        expected_test_count = _count_tests_in_config_for_bundle(
            config, bundle_system_name
        )
        assert expected_test_count >= 1, "Fixture must define at least one test"

        # Create a benchmark run (raw INSERT to avoid ORM FK resolution to "model" table)
        run_id = _insert_benchmark_run(session_manager, "integration-populate-test-run")
        assert run_id is not None

        # Before: no benchmark_run_test_bundle rows for this run
        assert _count_run_test_bundle_by_run_id(session_manager, run_id) == 0

        # Populate run bundle
        service = BenchmarkRunTestBundlePopulationService()
        pop_result = service.populate_run_bundle(run_id, bundle_system_name)

        assert pop_result["run_id"] == run_id
        assert pop_result["test_bundle_id"] is not None
        assert pop_result["inserted_count"] == expected_test_count

        # After: one row per test in the bundle
        assert _count_run_test_bundle_by_run_id(
            session_manager, run_id
        ) == expected_test_count

        rows = _get_run_test_bundle_rows(session_manager, run_id)
        assert len(rows) == expected_test_count
        # All rows should have the same test_bundle_id (the one we resolved)
        test_bundle_ids = {r[0] for r in rows}
        assert len(test_bundle_ids) == 1
        assert pop_result["test_bundle_id"] in test_bundle_ids
        # Each row has a distinct test_id (from benchmark_test_bundle_grouping)
        test_ids = [r[1] for r in rows]
        assert len(test_ids) == len(set(test_ids)), "Each row should have distinct test_id"

    def test_populate_run_bundle_with_two_tests(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path_two_tests,
    ):
        """
        Seed from a config with one bundle and two tests; populate_run_bundle
        creates two rows (one per test) with distinct test_ids.
        """
        assert config_path_two_tests.exists(), "Two-tests fixture must exist"
        session_manager = SessionManager.get_instance()

        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path_two_tests
        )
        assert result is True

        config = yaml.safe_load(config_path_two_tests.read_text())
        bundle_system_name = "minimal-bundle"
        expected_test_count = _count_tests_in_config_for_bundle(
            config, bundle_system_name
        )
        assert expected_test_count == 2, "Fixture must define exactly two tests"

        run_id = _insert_benchmark_run(
            session_manager, "integration-populate-two-tests-run"
        )
        assert _count_run_test_bundle_by_run_id(session_manager, run_id) == 0

        service = BenchmarkRunTestBundlePopulationService()
        pop_result = service.populate_run_bundle(run_id, bundle_system_name)

        assert pop_result["inserted_count"] == 2
        assert _count_run_test_bundle_by_run_id(session_manager, run_id) == 2

        rows = _get_run_test_bundle_rows(session_manager, run_id)
        assert len(rows) == 2
        test_bundle_ids = {r[0] for r in rows}
        assert len(test_bundle_ids) == 1
        test_ids = [r[1] for r in rows]
        assert len(set(test_ids)) == 2, "Two distinct test_ids expected"

    def test_populate_run_bundle_uses_newest_after_reload(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
        config_path_two_tests,
    ):
        """
        Seed with one-test config, populate run1 (1 row). Reload with two-test
        config (same bundle key), populate run2; run2 gets the newest state
        (2 rows from current groupings).
        """
        assert config_path.exists() and config_path_two_tests.exists()
        session_manager = SessionManager.get_instance()
        bundle_system_name = "minimal-bundle"

        # First seed: one test
        result1 = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert result1 is True

        run_id_1 = _insert_benchmark_run(
            session_manager, "integration-reload-run-1"
        )
        service = BenchmarkRunTestBundlePopulationService()
        pop1 = service.populate_run_bundle(run_id_1, bundle_system_name)
        assert pop1["inserted_count"] == 1
        assert _count_run_test_bundle_by_run_id(session_manager, run_id_1) == 1

        # Reload: seed with two-test config (same bundle, now two tests)
        result2 = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path_two_tests
        )
        assert result2 is True

        # Second run: should see newest state (two tests in bundle)
        run_id_2 = _insert_benchmark_run(
            session_manager, "integration-reload-run-2"
        )
        pop2 = service.populate_run_bundle(run_id_2, bundle_system_name)
        assert pop2["inserted_count"] == 2
        assert _count_run_test_bundle_by_run_id(session_manager, run_id_2) == 2

        rows2 = _get_run_test_bundle_rows(session_manager, run_id_2)
        assert len(rows2) == 2
        test_ids_2 = [r[1] for r in rows2]
        assert len(set(test_ids_2)) == 2
        # run1 still has only 1 row (unchanged)
        assert _count_run_test_bundle_by_run_id(session_manager, run_id_1) == 1
