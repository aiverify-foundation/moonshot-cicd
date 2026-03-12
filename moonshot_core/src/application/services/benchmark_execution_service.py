"""
Service for executing benchmarks.

This service handles the execution of benchmark tasks using TaskManager,
providing a clean interface for background task execution.
Internally handles async operations while providing a synchronous interface.
"""

import json
import asyncio
import multiprocessing
from datetime import datetime, timezone
from typing import List, Optional

from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.services.logger import configure_logger
from domain.services.task_manager import TaskManager


# Initialize logger for this module
logger = configure_logger(__name__)


def _run_bundle_in_process(
    bundle_id: str, connector: str, run_id: Optional[int] = None
) -> None:
    """
    Wrapper to run a bundle in a separate process.

    Instantiates BenchmarkExecutionService and calls execute_bundle.
    Used as the target for multiprocessing.Process (must be module-level to be picklable).

    Args:
        bundle_id: Bundle identifier to execute
        connector: Connector name to use
        run_id: Optional benchmark run id (from BenchmarkRunEntity) for this run.
            TODO: run_id will be required (non-optional) in the future.
    """
    execution_service = BenchmarkExecutionService()
    execution_service.execute_bundle(bundle_id, connector, run_id=run_id)


class BenchmarkExecutionService:
    """
    Service class for executing benchmark tasks.
    
    This service provides methods to execute benchmarks in the background,
    handling TaskManager initialization, parameter conversion, and error handling.
    """
    
    # This is where we should pass in references to the repositories
    def __init__(self):
        """Initialize the BenchmarkExecutionService."""
        logger.info("[BenchmarkExecutionService] Initializing BenchmarkExecutionService")

    def start_bundle_in_background(
        self,
        bundle_name: str,
        connector: str,
        run_id: Optional[int] = None,
    ) -> str:
        """
        Validate the bundle (DB only), start its execution in a daemon process, and return the bundle id.

        Resolves the bundle from the DB only (seeded config). Callers can map the returned
        bundle_id to a response DTO. Raises KeyError if the bundle is not found in the DB.

        Args:
            bundle_name: Bundle system name from the request (used to resolve the bundle in DB)
            connector: Connector name to use for the bundle
            run_id: Optional benchmark run id (from BenchmarkRunEntity) for the background process to use.
                TODO: run_id will be required (non-optional) in the future.

        Returns:
            The resolved bundle id (same as bundle_name).

        Raises:
            KeyError: If the bundle is not found in the DB.
        """
        from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (  # noqa: WPS433
            BenchmarkTestConfigAdapter,
        )

        config_adapter = BenchmarkTestConfigAdapter()
        try:
            config_adapter.get_bundle_id_by_system_name_latest(bundle_name)
        except ValueError:
            logger.error("Bundle with ID %r not found in DB. Seed bundles first.", bundle_name)
            raise KeyError(f"Bundle with ID '{bundle_name}' not found") from None

        process = multiprocessing.Process(
            target=_run_bundle_in_process,
            args=(bundle_name, connector, run_id),
        )
        process.daemon = True
        process.start()

        logger.info(
            f"[BenchmarkExecutionService] Bundle execution started in daemon process for bundle: {bundle_name}"
        )
        return bundle_name

    def start_benchmark_run(
        self,
        run_name: str,
        bundle_names: List[str],
        llm_provider_name: str,
        llm_provider_config_name: str,
    ) -> None:
        """
        Start a benchmark run: create a benchmark run entity, then execute multiple bundles
        in separate daemon processes, passing the run id for them to use.

        Uses a single run name, LLM provider name, and LLM provider config name for all bundles.
        The provider config name is used as the connector id for benchmark execution.

        Args:
            run_name: Name for this benchmark run.
            bundle_names: Names/ids of the bundles to execute.
            llm_provider_name: Name of the LLM provider (for logging).
            llm_provider_config_name: Name of the LLM provider config (connector id for execution).

        Raises:
            KeyError: If any bundle is not found.
        """
        from application.services.benchmark_run_service import BenchmarkRunService  # noqa: WPS433

        connector = llm_provider_config_name
        logger.info(
            f"[BenchmarkExecutionService] Starting benchmark run: run_name={run_name}, "
            f"llm_provider={llm_provider_name}, config={connector}, bundles={bundle_names}"
        )

        run_entity = BenchmarkRunEntity(
            name=run_name,
            status="running",
            endpoint_type="LLM_Provider",
            start_time=datetime.now(timezone.utc),
        )
        saved_run = BenchmarkRunService().save_run(run_entity)
        run_id = saved_run.id

        for bundle_name in bundle_names:
            #generate the benchmark run test bundle
            self.start_bundle_in_background(bundle_name, connector, run_id=run_id)

    def execute_bundle(
        self,
        bundle_id: str,
        connector: str,
        run_id: Optional[int] = None,
        write_to_db: bool = True,
    ) -> None:
        """
        Execute a bundle (multiple benchmark tests) synchronously and write a combined results file.

        Prefer DB path when the bundle exists in the database (seeded config): loads bundle and test
        list from DB, creates benchmark_run_test_status and benchmark_run_test_prompt for each test
        via BenchmarkRunTestSetupService, and passes the correct test_id into run_benchmark so
        prompts are read from the database. If the bundle is not in the DB, we look in the file
        (BenchmarkService.get_bundle_by_id(bundle_id)); if found there, we run using the file-based
        bundle with prompts from dataset load (no run_test/prompts created; test_id placeholder).
        If the bundle is in neither DB nor file, get_bundle_by_id raises KeyError and the error is logged.

        This follows the same combined JSON pattern as TaskManager.run_test:
        - run_metadata: run_id/test_id/start/end/duration
        - run_results: list of benchmark JSON results (one per test)

        Args:
            bundle_id: Bundle system name (e.g. minimal-bundle) for DB lookup, or bundle id for file fallback.
            connector: Connector name to use for all tests in the bundle.
            run_id: Optional benchmark run id (from BenchmarkRunEntity). Required for DB path; if None on DB path, a run is created.
            write_to_db: If True (default), run_benchmark writes results to DB when run_test/prompts exist. If False, prompts come from dataset load and no DB write.
        """
        try:
            logger.info(f"[BenchmarkExecutionService] Starting bundle execution for bundle: {bundle_id}")

            # Lazy imports to avoid heavy imports at module load and keep parity with api process execution
            from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (  # noqa: WPS433
                BenchmarkTestConfigAdapter,
            )
            from application.services.benchmark_run_test_setup_service import (  # noqa: WPS433
                BenchmarkRunTestSetupService,
            )
            from application.services.benchmark_run_service import BenchmarkRunService  # noqa: WPS433

            start_time = datetime.now()
            prompt_processor = "asyncio_prompt_processor_adapter"
            task_manager = TaskManager()
            config_adapter = BenchmarkTestConfigAdapter()
            setup_service = BenchmarkRunTestSetupService()
            effective_run_id: Optional[int] = run_id

            # Prefer DB path: bundle and tests from database, create run_test + prompts, pass real test_id.
            use_db_path = False
            test_tuples: list[tuple[int, str, str, dict]] = []  # (test_id, test_name, dataset_system_name, metric_dict)

            try:
                bundle_db_id = config_adapter.get_bundle_id_by_system_name_latest(bundle_id)
                test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_db_id)
                if not test_ids:
                    raise ValueError(f"Bundle has no tests: {bundle_id!r}")
                if write_to_db:
                    if effective_run_id is None:
                        run_name = f"Bundle run: {bundle_id}"
                        run_service = BenchmarkRunService()
                        existing_run = run_service.get_run_by_name(run_name)
                        if existing_run is not None and existing_run.id is not None:
                            effective_run_id = existing_run.id
                        else:
                            run_entity = BenchmarkRunEntity(
                                name=run_name,
                                status="running",
                                endpoint_type="LLM_Provider",
                                start_time=datetime.now(timezone.utc),
                            )
                            saved_run = run_service.save_run(run_entity)
                            effective_run_id = saved_run.id
                    for tid in test_ids:
                        setup_service.create_run_test_with_prompts(effective_run_id, tid)
                for tid in test_ids:
                    test_name, dataset_system_name, metric_name = config_adapter.get_test_info(tid)
                    test_tuples.append((tid, test_name, dataset_system_name, {"name": metric_name}))
                use_db_path = True
            except ValueError:
                # Bundle not in DB or has no tests: will look in file below (get_bundle_by_id) and use file-based bundle if found.
                pass

            if use_db_path:
                effective_run_id_str = str(effective_run_id) if effective_run_id is not None else bundle_id

                async def _run_all_db() -> list[str]:
                    results = []
                    for tid, test_name, dataset_system_name, metric_dict in test_tuples:
                        result = await task_manager.run_benchmark(
                            run_id=effective_run_id_str,
                            test_name=test_name,
                            dataset=dataset_system_name,
                            metric=metric_dict,
                            connector=connector,
                            prompt_processor=prompt_processor,
                            callback_fn=None,
                            write_result=False,
                            write_to_db=write_to_db,
                            db_run_id=effective_run_id if write_to_db else None,
                            test_id=tid,
                        )
                        results.append(result)
                    return results

                eval_results = asyncio.run(_run_all_db())
            else:
                # Look in file for bundle (benchmark source YAML); if found, run with file-based config.
                from application.services.benchmark import BenchmarkService  # noqa: WPS433

                benchmark_service = BenchmarkService(None, None)
                bundle = benchmark_service.get_bundle_by_id(bundle_id)
                effective_run_id_str = str(run_id) if run_id is not None else bundle_id

                async def _run_all_file() -> list[str]:
                    tasks = []
                    for test in bundle.tests:
                        tasks.append(
                            task_manager.run_benchmark(
                                run_id=effective_run_id_str,
                                test_name=test.id,
                                dataset=test.dataset.id if test.dataset else "",
                                metric=test.metric,
                                connector=connector,
                                prompt_processor=prompt_processor,
                                callback_fn=None,
                                write_result=False,
                                write_to_db=write_to_db,
                                db_run_id=run_id if write_to_db else None,
                                test_id=1,  # Placeholder: file path does not create run_test/prompts per test
                            )
                        )
                    return await asyncio.gather(*tasks)

                eval_results = asyncio.run(_run_all_file())

            # Record the end time and calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            json_results = [json.loads(result) for result in eval_results if result]

            if not json_results:
                logger.warning(
                    f"[BenchmarkExecutionService] Bundle completed but no results were returned "
                    f"for bundle: {bundle_id}"
                )
                return

            metadata_run_id = effective_run_id if use_db_path else (run_id if run_id is not None else bundle_id)
            run_metadata = {
                "run_metadata": {
                    "run_id": metadata_run_id,
                    "test_id": bundle_id,
                    "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration": duration,
                }
            }
            final_results = run_metadata | {"run_results": json_results}
            final_results_str = json.dumps(final_results, indent=4)

            result_path = task_manager._store_results_to_local_path(bundle_id, final_results_str)
            if result_path:
                logger.info(
                    f"[BenchmarkExecutionService] Bundle completed successfully for bundle: {bundle_id}. "
                    f"Results written to: {result_path}"
                )
            else:
                logger.error(f"[BenchmarkExecutionService] Failed to write results file for bundle: {bundle_id}")

        except Exception as e:
            logger.error(
                f"[BenchmarkExecutionService] Error executing bundle for bundle {bundle_id}: {str(e)}",
                exc_info=True,
            )
            # Don't re-raise the exception - background tasks should log errors but not crash
