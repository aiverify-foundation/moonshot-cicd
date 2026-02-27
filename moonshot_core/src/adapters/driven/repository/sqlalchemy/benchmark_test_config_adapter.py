"""SQLAlchemy adapter for seeding benchmark_test_bundle, benchmark_test, and benchmark_test_bundle_grouping."""

from typing import Optional

from domain.services.logger import configure_logger
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestDatasetModel,
    BenchmarkTestMetricModel,
    BenchmarkTestBundleModel,
    BenchmarkTestModel,
    BenchmarkTestBundleGroupingModel,
)


class BenchmarkTestConfigAdapter:
    """
    Adapter that persists benchmark test config (bundles, tests, groupings) to SQLAlchemy.

    Used by SharedConfigSeedService to fill benchmark_test_bundle, benchmark_test,
    and benchmark_test_bundle_grouping from shared.yaml. Uses SessionManager for DB access.
    """

    def __init__(self) -> None:
        self.session_manager = SessionManager.get_instance()
        self.logger = configure_logger(__name__)

    def get_or_create_metric(self, name: str) -> int:
        """
        Return metric id for the given name; create a new row if not present.

        Args:
            name: Metric name (e.g. refusal_adapter, accuracy_adapter).

        Returns:
            int: Primary key of benchmark_test_metric row.
        """
        with self.session_manager.get_session() as session:
            existing = (
                session.query(BenchmarkTestMetricModel)
                .filter(BenchmarkTestMetricModel.name == name)
                .first()
            )
            if existing:
                return existing.id
            new = BenchmarkTestMetricModel(name=name)
            session.add(new)
            session.flush()
            self.logger.info("Created metric: name=%r, id=%s", name, new.id)
            return new.id

    def get_dataset_id_by_system_name(
        self,
        system_name: str,
        version: int = 1,
    ) -> int:
        """
        Return benchmark_test_dataset.id for the given system_name (and optional version).

        Args:
            system_name: Dataset system_name (e.g. mlc-ailuminate-hte).
            version: Dataset version; default 1.

        Returns:
            int: Primary key of benchmark_test_dataset row.

        Raises:
            ValueError: If no dataset exists with that system_name (and version).
                Caller should seed datasets first via BenchmarkDatasetSeedService.
        """
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkTestDatasetModel)
                .filter(
                    BenchmarkTestDatasetModel.system_name == system_name,
                    BenchmarkTestDatasetModel.version == version,
                )
                .first()
            )
        if model is None:
            self.logger.error("Dataset not found: system_name=%r, version=%s", system_name, version)
            raise ValueError(
                f"Dataset not found: system_name={system_name!r}, version={version}. "
                "Seed datasets first via BenchmarkDatasetSeedService."
            )
        return model.id

    def get_dataset_id_by_system_name_latest(self, system_name: str) -> int:
        """
        Return benchmark_test_dataset.id for the given system_name (latest version).

        Args:
            system_name: Dataset system_name (e.g. mlc-ailuminate-hte).

        Returns:
            int: Primary key of the benchmark_test_dataset row with the highest version.

        Raises:
            ValueError: If no dataset exists with that system_name.
        """
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkTestDatasetModel)
                .filter(BenchmarkTestDatasetModel.system_name == system_name)
                .order_by(BenchmarkTestDatasetModel.version.desc())
                .first()
            )
            if model is None:
                self.logger.error(
                    "Dataset not found: system_name=%r (no version). Seed datasets first.",
                    system_name,
                )
                raise ValueError(
                    f"Dataset not found: system_name={system_name!r}. "
                    "Seed datasets first via BenchmarkDatasetSeedService."
                )
            dataset_id = model.id
        return dataset_id

    def get_bundle_id(self, version: int, system_name: str) -> Optional[int]:
        """
        Return benchmark_test_bundle.id for (version, system_name), or None if not found.
        """
        with self.session_manager.get_session() as session:
            row = (
                session.query(BenchmarkTestBundleModel)
                .filter(
                    BenchmarkTestBundleModel.version == version,
                    BenchmarkTestBundleModel.system_name == system_name,
                )
                .first()
            )
            return row.id if row else None

    def insert_bundle(
        self,
        version: int,
        system_name: str,
        name: str,
        description: Optional[str],
        category: str,
    ) -> int:
        """
        Insert a new benchmark_test_bundle row. Returns id.

        Args:
            version: Bundle version.
            system_name: Unique bundle key (e.g. undesirable-content).
            name: Display name.
            description: Optional description.
            category: Category (required).

        Returns:
            int: Primary key of the new benchmark_test_bundle row.
        """
        with self.session_manager.get_session() as session:
            new = BenchmarkTestBundleModel(
                version=version,
                system_name=system_name,
                name=name,
                description=description,
                category=category,
            )
            session.add(new)
            session.flush()
            self.logger.info("Created bundle: system_name=%r, id=%s", system_name, new.id)
            return new.id

    def update_bundle(
        self,
        version: int,
        system_name: str,
        name: str,
        description: Optional[str],
        category: str,
    ) -> int:
        """
        Update an existing benchmark_test_bundle by (version, system_name). Returns id.

        Raises:
            ValueError: If no row exists with that (version, system_name).
        """
        with self.session_manager.get_session() as session:
            existing = (
                session.query(BenchmarkTestBundleModel)
                .filter(
                    BenchmarkTestBundleModel.version == version,
                    BenchmarkTestBundleModel.system_name == system_name,
                )
                .first()
            )
            if existing is None:
                raise ValueError(
                    f"Bundle not found: version={version}, system_name={system_name!r}. "
                    "Cannot update; use insert_bundle first."
                )
            existing.name = name
            existing.description = description
            existing.category = category
            session.flush()
            self.logger.debug("Updated bundle: system_name=%r, id=%s", system_name, existing.id)
            return existing.id

    def get_test_id(self, version: int, system_name: str) -> Optional[int]:
        """
        Return benchmark_test.id for (version, system_name), or None if not found.
        """
        with self.session_manager.get_session() as session:
            row = (
                session.query(BenchmarkTestModel)
                .filter(
                    BenchmarkTestModel.version == version,
                    BenchmarkTestModel.system_name == system_name,
                )
                .first()
            )
            return row.id if row else None

    def insert_test(
        self,
        version: int,
        system_name: str,
        name: str,
        type_: str,
        dataset_id: int,
        metric_id: int,
    ) -> int:
        """
        Insert a new benchmark_test row. Returns id.

        Args:
            version: Test version.
            system_name: Unique test key (e.g. bundle_key__test_slug).
            name: Display name.
            type_: Test type (e.g. benchmark, scan).
            dataset_id: FK to benchmark_test_dataset.id.
            metric_id: FK to benchmark_test_metric.id.

        Returns:
            int: Primary key of the new benchmark_test row.
        """
        with self.session_manager.get_session() as session:
            new = BenchmarkTestModel(
                version=version,
                system_name=system_name,
                name=name,
                type=type_,
                dataset_id=dataset_id,
                metric_id=metric_id,
            )
            session.add(new)
            session.flush()
            self.logger.info("Created test: system_name=%r, id=%s", system_name, new.id)
            return new.id

    def update_test(
        self,
        version: int,
        system_name: str,
        name: str,
        type_: str,
        dataset_id: int,
        metric_id: int,
    ) -> int:
        """
        Update an existing benchmark_test by (version, system_name). Returns id.

        Raises:
            ValueError: If no row exists with that (version, system_name).
        """
        with self.session_manager.get_session() as session:
            existing = (
                session.query(BenchmarkTestModel)
                .filter(
                    BenchmarkTestModel.version == version,
                    BenchmarkTestModel.system_name == system_name,
                )
                .first()
            )
            if existing is None:
                raise ValueError(
                    f"Test not found: version={version}, system_name={system_name!r}. "
                    "Cannot update; use insert_test first."
                )
            existing.name = name
            existing.type = type_
            existing.dataset_id = dataset_id
            existing.metric_id = metric_id
            session.flush()
            self.logger.debug("Updated test: system_name=%r, id=%s", system_name, existing.id)
            return existing.id

    def grouping_exists(self, test_bundle_id: int, test_id: int) -> bool:
        """
        Return True if a benchmark_test_bundle_grouping row exists for (test_bundle_id, test_id).
        """
        with self.session_manager.get_session() as session:
            row = (
                session.query(BenchmarkTestBundleGroupingModel)
                .filter(
                    BenchmarkTestBundleGroupingModel.test_bundle_id == test_bundle_id,
                    BenchmarkTestBundleGroupingModel.test_id == test_id,
                )
                .first()
            )
            return row is not None

    def insert_grouping(self, test_bundle_id: int, test_id: int) -> None:
        """
        Insert a new benchmark_test_bundle_grouping row.

        Args:
            test_bundle_id: FK to benchmark_test_bundle.id.
            test_id: FK to benchmark_test.id.
        """
        with self.session_manager.get_session() as session:
            session.add(
                BenchmarkTestBundleGroupingModel(
                    test_bundle_id=test_bundle_id,
                    test_id=test_id,
                )
            )
            self.logger.debug("Created grouping: test_bundle_id=%s, test_id=%s", test_bundle_id, test_id)
