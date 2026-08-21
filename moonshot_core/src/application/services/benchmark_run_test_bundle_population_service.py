"""
Service that populates benchmark_run_test_bundle for a given run and test bundle.

The service performs all saves via the repository; the entity is data-only and never
saves itself.
"""

from domain.services.logger import get_logger

from typing import List, Optional

from domain.entities.benchmark_run_test_bundle_entity import BenchmarkRunTestBundleEntity
from application.ports.benchmark_run_test_bundle_repository import (
    BenchmarkRunTestBundleRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_bundle_adapter import (
    SqlAlchemyBenchmarkRunTestBundleRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)


class BenchmarkRunTestBundlePopulationService:
    """
    Populates benchmark_run_test_bundle rows for a run and test bundle.

    Resolves the test bundle by system_name (latest version) and inserts one row
    per (run_id, test_bundle_id, test_id) using the repository. The entity is
    never given a save method; the service builds the entity and calls
    repository.save(entity).
    """

    def __init__(
        self,
        run_test_bundle_repository: Optional[BenchmarkRunTestBundleRepository] = None,
        config_adapter: Optional[BenchmarkTestConfigAdapter] = None,
    ) -> None:
        self._repo = run_test_bundle_repository or SqlAlchemyBenchmarkRunTestBundleRepository()
        self._config = config_adapter or BenchmarkTestConfigAdapter()
        self.logger = get_logger(__name__)

    def insert_run_test_bundle(
        self,
        run_id: int,
        test_bundle_id: int,
        test_id: int,
    ) -> BenchmarkRunTestBundleEntity:
        """
        Insert a single benchmark_run_test_bundle row.

        The service builds the entity and calls the repository to persist.
        Duplicate (run_id, test_bundle_id, test_id) will raise when the DB
        unique constraint is violated.

        Args:
            run_id: FK to benchmark_run.id.
            test_bundle_id: FK to benchmark_test_bundle.id.
            test_id: FK to benchmark_test.id.

        Returns:
            The saved entity with id populated.
        """
        entity = BenchmarkRunTestBundleEntity(
            id=None,
            run_id=run_id,
            test_bundle_id=test_bundle_id,
            test_id=test_id,
        )
        return self._repo.save(entity)

    def populate_run_bundle(
        self,
        run_id: int,
        test_bundle_system_name: str,
        test_ids: Optional[List[int]] = None,
    ) -> dict:
        """
        Populate benchmark_run_test_bundle for the given run and bundle (latest version).

        Resolves test_bundle_id by system_name (latest version), gets test_ids from
        benchmark_test_bundle_grouping (all, or only ``test_ids`` when provided),
        then inserts one row per test via insert_run_test_bundle.

        Args:
            run_id: FK to benchmark_run.id.
            test_bundle_system_name: system_name of the bundle (e.g. undesirable-content).
            test_ids: When set, only these benchmark_test.id values are inserted (must be
                a non-empty subset of the bundle's tests). When None, all tests in the bundle.

        Returns:
            Dict with run_id, test_bundle_id, inserted_count.

        Raises:
            ValueError: If no bundle exists with that system_name.
        """
        test_bundle_id = self._config.get_bundle_id_by_system_name_latest(
            test_bundle_system_name
        )
        if test_ids is None:
            to_insert = self._config.get_test_ids_by_bundle_id(test_bundle_id)
        else:
            to_insert = test_ids
        inserted_count = 0
        for test_id in to_insert:
            self.insert_run_test_bundle(run_id, test_bundle_id, test_id)
            inserted_count += 1
        self.logger.info(
            "Populated run_bundle: run_id=%s, test_bundle_id=%s, inserted_count=%s",
            run_id,
            test_bundle_id,
            inserted_count,
        )
        return {
            "run_id": run_id,
            "test_bundle_id": test_bundle_id,
            "inserted_count": inserted_count,
        }
