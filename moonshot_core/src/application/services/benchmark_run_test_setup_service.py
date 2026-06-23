"""
Service that creates a run test status and all run test prompts for a (run, test) pair.

Given benchmark_run_id and benchmark_test_id, inserts one benchmark_run_test_status
and one benchmark_run_test_prompt per dataset prompt, with target and prompt filled.
"""

from domain.services.logger import get_logger

from typing import List, Optional

from application.ports.benchmark_run_test_prompt_repository import (
    BenchmarkRunTestPromptRepository,
)
from application.ports.benchmark_run_test_status_repository import (
    BenchmarkRunTestStatusRepository,
)
from application.ports.dataset_repository import DatasetRepository
from domain.entities.benchmark_run_test_prompt_entity import (
    BenchmarkRunTestPromptEntity,
)
from domain.entities.benchmark_run_test_status_entity import (
    BenchmarkRunTestStatusEntity,
)
from application.services.benchmark_run_test_status_service import (
    BenchmarkRunTestStatusService,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import (
    SqlAlchemyBenchmarkRunTestPromptRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.dataset_adapter import (
    SqlAlchemyDatasetRepository,
)


class BenchmarkRunTestSetupService:
    """
    Creates benchmark_run_test_status and benchmark_run_test_prompt rows for a run and test.

    Resolves the test's dataset, then inserts one run test status (not_started) and one
    run test prompt per dataset prompt with target and prompt_additional_info filled.
    """

    def __init__(
        self,
        status_service: Optional[BenchmarkRunTestStatusService] = None,
        status_repository: Optional[BenchmarkRunTestStatusRepository] = None,
        prompt_repository: Optional[BenchmarkRunTestPromptRepository] = None,
        config_adapter: Optional[BenchmarkTestConfigAdapter] = None,
        dataset_repository: Optional[DatasetRepository] = None,
    ) -> None:
        self._status_service = status_service or BenchmarkRunTestStatusService()
        self._status_repo = (
            status_repository or SqlAlchemyBenchmarkRunTestStatusRepository()
        )
        self._prompt_repo = prompt_repository or SqlAlchemyBenchmarkRunTestPromptRepository()
        self._config = config_adapter or BenchmarkTestConfigAdapter()
        self._dataset_repo = dataset_repository or SqlAlchemyDatasetRepository()
        self.logger = get_logger(__name__)

    def create_run_test_with_prompts(
        self,
        benchmark_run_id: int,
        benchmark_test_id: int,
    ) -> tuple[BenchmarkRunTestStatusEntity, List[BenchmarkRunTestPromptEntity]]:
        """
        Create one run test status and all run test prompts for the given run and test.

        Args:
            benchmark_run_id: FK to benchmark_run.id.
            benchmark_test_id: FK to benchmark_test.id.

        Returns:
            Tuple of (saved run test status entity, list of saved run test prompt entities).
            If (run_id, test_id) already exists, returns existing status and existing prompts
            without creating new rows.

        Raises:
            ValueError: If benchmark test is not found.
        """
        existing = self._status_repo.get_by_run_and_test(
            benchmark_run_id, benchmark_test_id
        )
        if existing is not None and existing.id is not None:
            existing_prompts = self._prompt_repo.get_all_by_run_test_id(existing.id)
            self.logger.info(
                "Run test already exists: run_id=%s test_id=%s run_test_id=%s, returning existing",
                benchmark_run_id,
                benchmark_test_id,
                existing.id,
            )
            return existing, existing_prompts

        dataset_id = self._config.get_test_dataset_id(benchmark_test_id)
        dataset_prompts = self._dataset_repo.get_prompts_by_dataset_id(dataset_id)

        status_entity = BenchmarkRunTestStatusEntity(
            run_id=benchmark_run_id,
            test_id=benchmark_test_id,
            status="not_started",
        )
        saved_status = self._status_service.save_run_test_status(status_entity)
        run_test_id = saved_status.id
        if run_test_id is None:
            run_test_id = 0  # defensive; save returns entity with id set

        saved_prompts: List[BenchmarkRunTestPromptEntity] = []
        for dp in dataset_prompts:
            prompt_entity = BenchmarkRunTestPromptEntity(
                run_test_id=run_test_id,
                prompt_id=dp.id if dp.id is not None else 0,
                status="pending",
                target=dp.target,
                prompt_additional_info=dp.prompt,
            )
            saved = self._prompt_repo.save(prompt_entity)
            saved_prompts.append(saved)

        self.logger.info(
            "Created run test with prompts: run_id=%s test_id=%s run_test_id=%s prompt_count=%s",
            benchmark_run_id,
            benchmark_test_id,
            run_test_id,
            len(saved_prompts),
        )
        return saved_status, saved_prompts
