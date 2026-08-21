"""Tests for BenchmarkTestConfigAdapter (real DB, get_dataset_id_by_system_name_latest)."""

from typing import Optional

import pytest
from pathlib import Path

from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestDatasetModel,
    BenchmarkTestBundleModel,
    BenchmarkTestBundleGroupingModel,
    BenchmarkTestModel,
    BenchmarkTestMetricModel,
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


def _insert_bundle(
    session_manager,
    system_name: str,
    version: int,
    name: str = "Test Bundle",
    description: Optional[str] = None,
    category: str = "category",
    visible: bool = True,
) -> int:
    """Insert a BenchmarkTestBundleModel row and return its id."""
    with session_manager.get_session() as session:
        model = BenchmarkTestBundleModel(
            version=version,
            system_name=system_name,
            name=name,
            description=description,
            category=category,
            visible=visible,
        )
        session.add(model)
        session.flush()
        return model.id


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


class TestBenchmarkTestConfigAdapterGetBundleIdBySystemNameLatest:
    """Tests for get_bundle_id_by_system_name_latest."""

    def test_get_bundle_id_by_system_name_latest_returns_id(
        self, benchmark_config_adapter
    ):
        """Returns the id of the inserted bundle for the given system_name."""
        session_manager = benchmark_config_adapter.session_manager
        inserted_id = _insert_bundle(session_manager, "test-bundle", 1)

        result = benchmark_config_adapter.get_bundle_id_by_system_name_latest(
            "test-bundle"
        )

        assert result == inserted_id

    def test_get_bundle_id_by_system_name_latest_returns_highest_version(
        self, benchmark_config_adapter
    ):
        """When multiple rows exist for same system_name, returns id of row with highest version."""
        session_manager = benchmark_config_adapter.session_manager
        id_v1 = _insert_bundle(session_manager, "multi-bundle", 1)
        id_v2 = _insert_bundle(session_manager, "multi-bundle", 2)

        result = benchmark_config_adapter.get_bundle_id_by_system_name_latest(
            "multi-bundle"
        )

        assert result == id_v2

    def test_get_bundle_id_by_system_name_latest_raises_when_not_found(
        self, benchmark_config_adapter
    ):
        """Raises ValueError with 'Bundle not found' when no row exists for system_name."""
        with pytest.raises(ValueError, match="Bundle not found"):
            benchmark_config_adapter.get_bundle_id_by_system_name_latest(
                "nonexistent-bundle"
            )


class TestBenchmarkTestConfigAdapterGetTestIdsByBundleId:
    """Tests for get_test_ids_by_bundle_id."""

    def test_get_test_ids_by_bundle_id_returns_empty_when_no_groupings(
        self, benchmark_config_adapter
    ):
        """Returns empty list when bundle has no groupings."""
        session_manager = benchmark_config_adapter.session_manager
        bundle_id = _insert_bundle(session_manager, "empty-bundle", 1)

        result = benchmark_config_adapter.get_test_ids_by_bundle_id(bundle_id)

        assert result == []

    def test_get_test_ids_by_bundle_id_returns_test_ids(
        self, benchmark_config_adapter
    ):
        """Returns list of test_id for all groupings of the bundle."""
        session_manager = benchmark_config_adapter.session_manager
        # Need metric and dataset for benchmark_test FK
        with session_manager.get_session() as session:
            metric = BenchmarkTestMetricModel(name="test_metric")
            session.add(metric)
            session.flush()
            metric_id = metric.id
            dataset = BenchmarkTestDatasetModel(
                system_name="ds",
                version=1,
                description=None,
                license=None,
                reference=None,
            )
            session.add(dataset)
            session.flush()
            dataset_id = dataset.id
            t1 = BenchmarkTestModel(
                version=1,
                system_name="t1",
                name="T1",
                type="benchmark",
                dataset_id=dataset_id,
                metric_id=metric_id,
            )
            session.add(t1)
            session.flush()
            test_id_1 = t1.id
            t2 = BenchmarkTestModel(
                version=1,
                system_name="t2",
                name="T2",
                type="benchmark",
                dataset_id=dataset_id,
                metric_id=metric_id,
            )
            session.add(t2)
            session.flush()
            test_id_2 = t2.id
            bundle = BenchmarkTestBundleModel(
                version=1,
                system_name="bundle-with-tests",
                name="Bundle",
                description=None,
                category="cat",
            )
            session.add(bundle)
            session.flush()
            bundle_id = bundle.id
            session.add(
                BenchmarkTestBundleGroupingModel(
                    test_bundle_id=bundle_id,
                    test_id=test_id_1,
                )
            )
            session.add(
                BenchmarkTestBundleGroupingModel(
                    test_bundle_id=bundle_id,
                    test_id=test_id_2,
                )
            )

        result = benchmark_config_adapter.get_test_ids_by_bundle_id(bundle_id)

        assert set(result) == {test_id_1, test_id_2}
        assert len(result) == 2


class TestBenchmarkTestConfigAdapterGetTestDatasetId:
    """Tests for get_test_dataset_id."""

    def test_get_test_dataset_id_returns_dataset_id(
        self, benchmark_config_adapter
    ):
        """Returns dataset_id for the given benchmark_test id."""
        session_manager = benchmark_config_adapter.session_manager
        with session_manager.get_session() as session:
            metric = BenchmarkTestMetricModel(name="metric_get_ds")
            session.add(metric)
            session.flush()
            dataset = BenchmarkTestDatasetModel(
                system_name="ds_get_ds",
                version=1,
                description=None,
                license=None,
                reference=None,
            )
            session.add(dataset)
            session.flush()
            dataset_id = dataset.id
            test = BenchmarkTestModel(
                version=1,
                system_name="test_get_ds",
                name="Test",
                type="benchmark",
                dataset_id=dataset_id,
                metric_id=metric.id,
            )
            session.add(test)
            session.flush()
            test_id = test.id

        result = benchmark_config_adapter.get_test_dataset_id(test_id)

        assert result == dataset_id

    def test_get_test_dataset_id_raises_when_test_not_found(
        self, benchmark_config_adapter
    ):
        """Raises ValueError when no benchmark test exists with that id."""
        with pytest.raises(ValueError, match="Benchmark test not found"):
            benchmark_config_adapter.get_test_dataset_id(999999)


class TestBenchmarkTestConfigAdapterGetTestInfo:
    """Tests for get_test_info."""

    def test_get_test_info_returns_name_dataset_metric(
        self, benchmark_config_adapter
    ):
        """Returns (test_name, dataset_system_name, metric_name) for the given test_id."""
        session_manager = benchmark_config_adapter.session_manager
        with session_manager.get_session() as session:
            metric = BenchmarkTestMetricModel(name="refusal_adapter")
            session.add(metric)
            session.flush()
            dataset = BenchmarkTestDatasetModel(
                system_name="test_sample_dataset",
                version=1,
                description=None,
                license=None,
                reference=None,
            )
            session.add(dataset)
            session.flush()
            test = BenchmarkTestModel(
                version=1,
                system_name="sample_test",
                name="Sample Test",
                type="benchmark",
                dataset_id=dataset.id,
                metric_id=metric.id,
            )
            session.add(test)
            session.flush()
            test_id = test.id

        result = benchmark_config_adapter.get_test_info(test_id)

        assert result == ("Sample Test", "test_sample_dataset", "refusal_adapter")

    def test_get_test_info_raises_when_test_not_found(
        self, benchmark_config_adapter
    ):
        """Raises ValueError when no benchmark test exists with that id."""
        with pytest.raises(ValueError, match="Benchmark test not found"):
            benchmark_config_adapter.get_test_info(999999)
