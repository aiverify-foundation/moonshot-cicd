"""SQLAlchemy adapter for seeding benchmark_test_bundle, benchmark_test, and benchmark_test_bundle_grouping."""

from domain.services.logger import get_logger

from typing import Optional

from sqlalchemy.exc import IntegrityError

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
        self.logger = get_logger(__name__)

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

    def get_bundle_id_by_system_name_latest(self, system_name: str) -> int:
        """
        Return benchmark_test_bundle.id for the given system_name (latest version).

        Args:
            system_name: Bundle system_name (e.g. undesirable-content).

        Returns:
            int: Primary key of the benchmark_test_bundle row with the highest version.

        Raises:
            ValueError: If no bundle exists with that system_name.
        """
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkTestBundleModel)
                .filter(BenchmarkTestBundleModel.system_name == system_name)
                .order_by(BenchmarkTestBundleModel.version.desc())
                .first()
            )
            if model is None:
                self.logger.error(
                    "Bundle not found: system_name=%r (no version). Seed bundles first.",
                    system_name,
                )
                raise ValueError(
                    f"Bundle not found: system_name={system_name!r}. "
                    "Seed bundles first via SharedConfigSeedService."
                )
            return model.id

    def get_test_ids_by_bundle_id(self, test_bundle_id: int) -> list[int]:
        """
        Return list of benchmark_test.id for all tests in the given bundle.

        Args:
            test_bundle_id: FK to benchmark_test_bundle.id.

        Returns:
            List of test_id; empty if the bundle has no groupings.
        """
        with self.session_manager.get_session() as session:
            rows = (
                session.query(BenchmarkTestBundleGroupingModel.test_id)
                .filter(
                    BenchmarkTestBundleGroupingModel.test_bundle_id == test_bundle_id,
                )
                .all()
            )
            return [r[0] for r in rows]

    def insert_bundle(
        self,
        version: int,
        system_name: str,
        name: str,
        description: Optional[str],
        category: str,
        visible: bool = True,
    ) -> int:
        """
        Insert a new benchmark_test_bundle row. Returns id.

        Args:
            version: Bundle version.
            system_name: Unique bundle key (e.g. undesirable-content).
            name: Display name.
            description: Optional description.
            category: Category (required).
            visible: Whether the bundle appears in portal listing APIs.

        Returns:
            int: Primary key of the new benchmark_test_bundle row.

        Raises:
            ValueError: If a bundle already exists for (version, system_name).
        """
        with self.session_manager.get_session() as session:
            try:
                new = BenchmarkTestBundleModel(
                    version=version,
                    system_name=system_name,
                    name=name,
                    description=description,
                    category=category,
                    visible=visible,
                )
                session.add(new)
                session.flush()
                self.logger.info("Created bundle: system_name=%r, id=%s", system_name, new.id)
                return new.id
            except IntegrityError as e:
                session.rollback()
                self.logger.warning(
                    "Bundle already exists: version=%s, system_name=%r",
                    version,
                    system_name,
                )
                raise ValueError(
                    f"Bundle already exists for version={version}, system_name={system_name!r}. "
                    "Use get_bundle_id to retrieve the existing id."
                ) from e

    def update_bundle(
        self,
        bundle_id: int,
        *,
        name: str,
        description: Optional[str],
        category: str,
        visible: bool,
    ) -> None:
        """Update display fields and visibility for an existing bundle row."""
        with self.session_manager.get_session() as session:
            row = (
                session.query(BenchmarkTestBundleModel)
                .filter(BenchmarkTestBundleModel.id == bundle_id)
                .first()
            )
            if row is None:
                raise ValueError(f"Bundle not found: id={bundle_id}")
            row.name = name
            row.description = description
            row.category = category
            row.visible = visible
            session.flush()
            self.logger.debug(
                "Updated bundle id=%s system_name=%r visible=%s",
                bundle_id,
                row.system_name,
                visible,
            )

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

    def get_test_dataset_id(self, test_id: int) -> int:
        """
        Return benchmark_test_dataset.id for the given benchmark_test.id.

        Args:
            test_id: FK to benchmark_test.id.

        Returns:
            int: The dataset_id (benchmark_test_dataset.id) for that test.

        Raises:
            ValueError: If no benchmark test exists with that id.
        """
        with self.session_manager.get_session() as session:
            row = (
                session.query(BenchmarkTestModel)
                .filter(BenchmarkTestModel.id == test_id)
                .first()
            )
            if row is None:
                self.logger.error("Benchmark test not found: test_id=%s", test_id)
                raise ValueError(f"Benchmark test not found: test_id={test_id}")
            return row.dataset_id

    def get_test_info(self, test_id: int) -> tuple[str, str, str]:
        """
        Return (test_name, dataset_system_name, metric_name) for the given benchmark_test.id.

        Used by execute_bundle to call run_benchmark with DB-backed test config.

        Args:
            test_id: FK to benchmark_test.id.

        Returns:
            Tuple of (test display name, dataset system_name for loader, metric name).

        Raises:
            ValueError: If no benchmark test exists with that id.
        """
        with self.session_manager.get_session() as session:
            row = (
                session.query(BenchmarkTestModel)
                .filter(BenchmarkTestModel.id == test_id)
                .first()
            )
            if row is None:
                self.logger.error("Benchmark test not found: test_id=%s", test_id)
                raise ValueError(f"Benchmark test not found: test_id={test_id}")
            # Access relationships inside session (lazy load)
            dataset_system_name = row.dataset.system_name if row.dataset else ""
            metric_name = row.metric.name if row.metric else ""
            return (row.name, dataset_system_name, metric_name)

    def insert_test(
        self,
        version: int,
        system_name: str,
        name: str,
        type_: str,
        dataset_id: int,
        metric_id: int,
        description: Optional[str] = None,
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
            description: Optional long-form test description from YAML.

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
                description=description,
            )
            session.add(new)
            session.flush()
            self.logger.info("Created test: system_name=%r, id=%s", system_name, new.id)
            return new.id

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
