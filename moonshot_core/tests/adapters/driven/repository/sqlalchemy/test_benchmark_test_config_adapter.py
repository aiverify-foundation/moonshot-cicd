"""Tests for BenchmarkTestConfigAdapter (real DB, get_dataset_id_by_system_name_latest)."""

import pytest
from pathlib import Path

from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestDatasetModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager


@pytest.fixture(scope="function")
def test_db_path():
    """Create a temporary database path for testing."""
    moonshot_core_root: Path = (
        Path(__file__).parent.parent.parent.parent.parent.parent
    )
    db_path: Path = moonshot_core_root / "data" / "database" / "moonshot_pytest.db"

    if db_path.exists():
        db_path.unlink()

    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set up test database environment variable and reset SessionManager."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()

    yield

    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def benchmark_config_adapter(test_db_env):
    """Create a BenchmarkTestConfigAdapter with real SessionManager (migrations run on first use)."""
    return BenchmarkTestConfigAdapter()


def _insert_dataset(session_manager, system_name: str, version: int) -> int:
    """Insert a BenchmarkTestDatasetModel row and return its id."""
    with session_manager.get_session() as session:
        model = BenchmarkTestDatasetModel(
            system_name=system_name,
            version=version,
            description=None,
            license=None,
            reference=None,
        )
        session.add(model)
        session.flush()
        pk = model.id
    return pk


class TestBenchmarkTestConfigAdapterGetDatasetIdBySystemNameLatest:
    """Tests for get_dataset_id_by_system_name_latest."""

    def test_get_dataset_id_by_system_name_latest_returns_id(
        self, benchmark_config_adapter
    ):
        """Returns the id of the inserted row for the given system_name."""
        session_manager = benchmark_config_adapter.session_manager
        inserted_id = _insert_dataset(session_manager, "test-ds", 1)

        result = benchmark_config_adapter.get_dataset_id_by_system_name_latest(
            "test-ds"
        )

        assert result == inserted_id

    def test_get_dataset_id_by_system_name_latest_returns_highest_version(
        self, benchmark_config_adapter
    ):
        """When multiple rows exist for same system_name, returns id of row with highest version."""
        session_manager = benchmark_config_adapter.session_manager
        id_v1 = _insert_dataset(session_manager, "multi", 1)
        id_v2 = _insert_dataset(session_manager, "multi", 2)

        result = benchmark_config_adapter.get_dataset_id_by_system_name_latest(
            "multi"
        )

        assert result == id_v2

    def test_get_dataset_id_by_system_name_latest_raises_when_not_found(
        self, benchmark_config_adapter
    ):
        """Raises ValueError with 'Dataset not found' when no row exists for system_name."""
        with pytest.raises(ValueError, match="Dataset not found"):
            benchmark_config_adapter.get_dataset_id_by_system_name_latest(
                "nonexistent"
            )
