"""
Integration tests for SharedConfigSeedService.seed_if_test_file_changed.

Full flow: real FileSharedConfigRepository, FileDatasetRepository,
MoonshotConfigAdapter, SqlAlchemyDatasetRepository, BenchmarkDatasetSeedService,
and SharedConfigSeedService with a test DB. Uses a minimal shared config fixture
that references only test_sample_dataset.
"""

from pathlib import Path

import pytest
import yaml

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestDatasetModel,
    BenchmarkTestBundleModel,
    BenchmarkTestModel,
    MoonshotConfigModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.shared_config_seed_service import (
    SharedConfigSeedService,
    SHARED_CONFIG_SEED_VERSION_KEY,
    TEST_FILE_LAST_MODIFIED_KEY,
)
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
    moonshot_core_root = (
        Path(__file__).resolve().parent.parent.parent.parent
    )
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
    """Path to minimal shared config that references only test_sample_dataset."""
    return (
        Path(__file__).resolve().parent
        / "fixtures"
        / "shared_minimal.yaml"
    )


@pytest.fixture
def shared_config_seed_service(test_db_env, config_path):
    """Build SharedConfigSeedService with full stack for seed_if_test_file_changed."""
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


def _count_table(session_manager, model):
    """Return number of rows for the given model."""
    with session_manager.get_session() as session:
        return session.query(model).count()


def _get_moonshot_config_value(session_manager, key: str):
    """Return value for key from moonshot_config, or None."""
    with session_manager.get_session() as session:
        row = (
            session.query(MoonshotConfigModel)
            .filter(MoonshotConfigModel.key == key)
            .first()
        )
        return row.value if row else None


def _has_dataset_system_name(session_manager, system_name: str) -> bool:
    """Return True if benchmark_test_dataset has a row with the given system_name."""
    with session_manager.get_session() as session:
        return (
            session.query(BenchmarkTestDatasetModel)
            .filter(BenchmarkTestDatasetModel.system_name == system_name)
            .first()
            is not None
        )


def _has_test_with_dataset_id(session_manager) -> bool:
    """Return True if at least one benchmark_test has non-null dataset_id."""
    with session_manager.get_session() as session:
        return (
            session.query(BenchmarkTestModel)
            .filter(BenchmarkTestModel.dataset_id.isnot(None))
            .first()
            is not None
        )


def _dataset_names_from_config(config: dict) -> set[str]:
    """Return unique dataset names referenced in the shared config."""
    names: set[str] = set()
    for bundle_data in config.values():
        if not isinstance(bundle_data, dict):
            continue
        for test in bundle_data.get("tests") or []:
            if isinstance(test, dict) and test.get("dataset"):
                names.add(test["dataset"])
    return names


@pytest.mark.integration
class TestSharedConfigSeedServiceConditionalIntegration:
    """Integration tests for SharedConfigSeedService.seed_if_test_file_changed."""

    def test_conditional_seed_runs_and_creates_bundles_tests(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
    ):
        """
        seed_if_test_file_changed runs (first run), creates dataset/bundle/test rows
        and sets test_file_last_modified in moonshot_config.
        """
        assert config_path.exists(), "Minimal fixture YAML must exist"
        session_manager = SessionManager.get_instance()

        result = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )

        assert result is True
        config = yaml.safe_load(config_path.read_text())
        expected_datasets = _dataset_names_from_config(config)
        for name in expected_datasets:
            assert _has_dataset_system_name(
                session_manager, name
            ), f"Expected benchmark_test_dataset row with system_name={name!r}"
        assert _count_table(session_manager, BenchmarkTestBundleModel) >= 1
        assert _count_table(session_manager, BenchmarkTestModel) >= 1
        assert _has_test_with_dataset_id(
            session_manager
        ), "Expected at least one benchmark_test with non-null dataset_id"
        assert (
            _get_moonshot_config_value(
                session_manager, TEST_FILE_LAST_MODIFIED_KEY
            )
            is not None
        ), "Expected moonshot_config to have test_file_last_modified set"

    def test_conditional_seed_returns_false_when_file_unchanged(
        self,
        shared_config_seed_service,
        config_path,
    ):
        """Second call without changing the file returns False (skip path)."""
        first = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert first is True

        second = shared_config_seed_service.seed_if_test_file_changed(
            config_path=config_path
        )
        assert second is False

    def test_conditional_seed_runs_again_after_config_file_modified(
        self,
        shared_config_seed_service,
        test_db_env,
        config_path,
        tmp_path,
    ):
        """
        After modifying the shared config file, seed_if_test_file_changed runs again
        (returns True) and DB remains consistent (all datasets, test_file_last_modified).
        """
        assert config_path.exists(), "Minimal fixture YAML must exist"
        temp_config = tmp_path / "shared.yaml"
        temp_config.write_text(config_path.read_text())

        first = shared_config_seed_service.seed_if_test_file_changed(
            config_path=temp_config
        )
        assert first is True

        second = shared_config_seed_service.seed_if_test_file_changed(
            config_path=temp_config
        )
        assert second is False

        temp_config.write_text(temp_config.read_text() + "\n# modified\n")

        third = shared_config_seed_service.seed_if_test_file_changed(
            config_path=temp_config
        )
        assert third is True

        session_manager = SessionManager.get_instance()
        config = yaml.safe_load(temp_config.read_text())
        expected_datasets = _dataset_names_from_config(config)
        for name in expected_datasets:
            assert _has_dataset_system_name(
                session_manager, name
            ), f"Expected benchmark_test_dataset row with system_name={name!r}"
        assert (
            _get_moonshot_config_value(
                session_manager, TEST_FILE_LAST_MODIFIED_KEY
            )
            is not None
        ), "Expected moonshot_config to have test_file_last_modified set"

    def test_reseed_drops_removed_bundle_and_honors_visible_false(
        self,
        shared_config_seed_service,
        test_db_env,
        tmp_path,
    ):
        """Bundles removed from YAML are not at the new seed version; visible:false is stored."""
        v1 = {
            "listed-bundle": {
                "name": "Listed",
                "category": "c",
                "tests": [
                    {
                        "name": "T1",
                        "type": "benchmark",
                        "dataset": "test_sample_dataset",
                        "metric": {"name": "refusal_adapter"},
                    },
                ],
            },
            "removed-bundle": {
                "name": "Removed",
                "category": "c",
                "tests": [
                    {
                        "name": "T2",
                        "type": "benchmark",
                        "dataset": "test_sample_dataset",
                        "metric": {"name": "refusal_adapter"},
                    },
                ],
            },
        }
        path = tmp_path / "visibility.yaml"
        path.write_text(yaml.dump(v1))
        assert shared_config_seed_service.seed_if_test_file_changed(config_path=path)

        v2 = {
            "listed-bundle": {
                "name": "Listed",
                "category": "c",
                "visible": False,
                "tests": v1["listed-bundle"]["tests"],
            },
            "new-bundle": {
                "name": "New",
                "category": "c",
                "tests": [
                    {
                        "name": "T3",
                        "type": "benchmark",
                        "dataset": "test_sample_dataset",
                        "metric": {"name": "refusal_adapter"},
                    },
                ],
            },
        }
        path.write_text(yaml.dump(v2) + "\n")
        assert shared_config_seed_service.seed_if_test_file_changed(config_path=path)

        session_manager = SessionManager.get_instance()
        seed_version = int(
            _get_moonshot_config_value(session_manager, SHARED_CONFIG_SEED_VERSION_KEY)
        )
        with session_manager.get_session() as session:
            rows = (
                session.query(BenchmarkTestBundleModel)
                .filter(BenchmarkTestBundleModel.version == seed_version)
                .all()
            )
            visible_by_name = {r.system_name: r.visible for r in rows}
        assert set(visible_by_name) == {"listed-bundle", "new-bundle"}
        assert visible_by_name["listed-bundle"] is False
        assert visible_by_name["new-bundle"] is True
