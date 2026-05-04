"""Load benchmark bundles and tests from the database (seeded shared config)."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestBundleGroupingModel,
    BenchmarkTestBundleModel,
    BenchmarkTestModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.benchmark_repository import BenchmarkRepository
from application.ports.dataset_repository import DatasetRepository
from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.test_bundle_entity import TestBundleEntity
from domain.services.logger import configure_logger


class SqlAlchemyBenchmarkRepository(BenchmarkRepository):
    """
    BenchmarkRepository backed by benchmark_test_bundle, benchmark_test, and related tables.

    Uses the latest ``version`` row per ``system_name`` for bundles and tests.
    """

    def __init__(self, dataset_repository: DatasetRepository) -> None:
        super().__init__(None)
        self._dataset_repository = dataset_repository
        self._session_manager = SessionManager.get_instance()
        self._logger = configure_logger(__name__)

    def get_dataset_by_id(self, dataset_id: str) -> DatasetEntity:
        return self._dataset_repository.get_dataset_by_id(dataset_id)

    def _test_entity_from_row(self, row: BenchmarkTestModel) -> BenchmarkTestEntity:
        metric_name = row.metric.name if row.metric else ""
        desc = (row.description or "").strip() if row.description else ""
        dataset_entity = None
        if row.dataset_id is not None:
            dataset_entity = self._dataset_repository.get_dataset_by_id(str(row.dataset_id))
        return BenchmarkTestEntity(
            id=row.name,
            name=row.name,
            dataset=dataset_entity,
            metric={"name": metric_name} if metric_name else {},
            description=desc,
            benchmark_test_id=row.id,
        )

    def get_all_bundles(self) -> list[TestBundleEntity]:
        with self._session_manager.get_session() as session:
            bundle_versions = (
                session.query(
                    BenchmarkTestBundleModel.system_name,
                    func.max(BenchmarkTestBundleModel.version).label("max_v"),
                )
                .group_by(BenchmarkTestBundleModel.system_name)
                .subquery()
            )
            bundles = (
                session.query(BenchmarkTestBundleModel)
                .join(
                    bundle_versions,
                    (BenchmarkTestBundleModel.system_name == bundle_versions.c.system_name)
                    & (BenchmarkTestBundleModel.version == bundle_versions.c.max_v),
                )
                .order_by(BenchmarkTestBundleModel.system_name)
                .all()
            )

            result: list[TestBundleEntity] = []
            for bundle in bundles:
                groupings = (
                    session.query(BenchmarkTestBundleGroupingModel)
                    .filter(
                        BenchmarkTestBundleGroupingModel.test_bundle_id == bundle.id,
                    )
                    .options(
                        joinedload(BenchmarkTestBundleGroupingModel.test).joinedload(
                            BenchmarkTestModel.metric
                        ),
                    )
                    .order_by(BenchmarkTestBundleGroupingModel.id)
                    .all()
                )
                tests: list[BenchmarkTestEntity] = []
                for g in groupings:
                    if g.test is None:
                        continue
                    tests.append(self._test_entity_from_row(g.test))
                result.append(
                    TestBundleEntity(
                        id=bundle.system_name,
                        name=bundle.name,
                        description=bundle.description or "",
                        category=bundle.category or "",
                        tests=tests,
                    )
                )
            return result

    def get_bundle_by_id(self, bundle_id: str) -> TestBundleEntity:
        with self._session_manager.get_session() as session:
            bundle = (
                session.query(BenchmarkTestBundleModel)
                .filter(BenchmarkTestBundleModel.system_name == bundle_id)
                .order_by(BenchmarkTestBundleModel.version.desc())
                .first()
            )
            if bundle is None:
                self._logger.error("Bundle not found in DB: system_name=%r", bundle_id)
                raise KeyError(f"Bundle with ID '{bundle_id}' not found")

            groupings = (
                session.query(BenchmarkTestBundleGroupingModel)
                .filter(BenchmarkTestBundleGroupingModel.test_bundle_id == bundle.id)
                .options(
                    joinedload(BenchmarkTestBundleGroupingModel.test).joinedload(
                        BenchmarkTestModel.metric
                    ),
                )
                .order_by(BenchmarkTestBundleGroupingModel.id)
                .all()
            )
            tests = [self._test_entity_from_row(g.test) for g in groupings if g.test is not None]
            return TestBundleEntity(
                id=bundle.system_name,
                name=bundle.name,
                description=bundle.description or "",
                category=bundle.category or "",
                tests=tests,
            )

    def get_all_benchmark_tests(self) -> list[BenchmarkTestEntity]:
        with self._session_manager.get_session() as session:
            test_versions = (
                session.query(
                    BenchmarkTestModel.system_name,
                    func.max(BenchmarkTestModel.version).label("max_v"),
                )
                .group_by(BenchmarkTestModel.system_name)
                .subquery()
            )
            rows = (
                session.query(BenchmarkTestModel)
                .join(
                    test_versions,
                    (BenchmarkTestModel.system_name == test_versions.c.system_name)
                    & (BenchmarkTestModel.version == test_versions.c.max_v),
                )
                .options(joinedload(BenchmarkTestModel.metric))
                .order_by(BenchmarkTestModel.system_name)
                .all()
            )
            return [self._test_entity_from_row(r) for r in rows]

    def get_benchmark_test_by_id(self, benchmark_test_id: str) -> BenchmarkTestEntity:
        with self._session_manager.get_session() as session:
            row = (
                session.query(BenchmarkTestModel)
                .options(joinedload(BenchmarkTestModel.metric))
                .filter(BenchmarkTestModel.system_name == benchmark_test_id)
                .order_by(BenchmarkTestModel.version.desc())
                .first()
            )
            if row is None:
                row = (
                    session.query(BenchmarkTestModel)
                    .options(joinedload(BenchmarkTestModel.metric))
                    .filter(BenchmarkTestModel.name == benchmark_test_id)
                    .order_by(BenchmarkTestModel.version.desc())
                    .first()
                )
        if row is None:
            self._logger.error("Benchmark test not found in DB: %r", benchmark_test_id)
            raise KeyError(f"Test configuration with ID '{benchmark_test_id}' not found")
        return self._test_entity_from_row(row)
