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
from typing import Dict, List, Optional

from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.session_manager import set_skip_alembic_upgrade
from application.services.benchmark import BenchmarkService
from application.services.benchmark_run_service import BenchmarkRunService
from application.services.benchmark_run_test_bundle_population_service import (
    BenchmarkRunTestBundlePopulationService,
)
from application.services.benchmark_run_test_setup_service import (
    BenchmarkRunTestSetupService,
)
from application.services.database_connector_config_service import (
    DatabaseConnectorConfigError,
    DatabaseConnectorConfigService,
)
from application.services.database_custom_app_connector_config_service import (
    DatabaseCustomAppConnectorConfigError,
    DatabaseCustomAppConnectorConfigService,
)
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from domain.services.logger import configure_logger
from domain.services.task_manager import TaskManager


# Initialize logger for this module
logger = configure_logger(__name__)


class BenchmarkRunTestSelectionError(ValueError):
    """Raised when ``tests_by_bundle`` references invalid or out-of-bundle test ids."""


def _bundle_names_to_resolved_test_ids(
    bundle_names: List[str],
    tests_by_bundle: Optional[Dict[str, List[int]]],
    config_adapter: BenchmarkTestConfigAdapter,
) -> Dict[str, List[int]]:
    """
    Resolve each bundle to the list of benchmark_test.id values to execute.

    Raises:
        KeyError: If a bundle system_name is not found in the database.
        BenchmarkRunTestSelectionError: If a bundle has no tests or selection is invalid.
    """
    resolved: Dict[str, List[int]] = {}
    for name in bundle_names:
        try:
            bundle_db_id = config_adapter.get_bundle_id_by_system_name_latest(name)
        except ValueError as e:
            raise KeyError(f"Bundle with ID '{name}' not found") from e
        all_ids = config_adapter.get_test_ids_by_bundle_id(bundle_db_id)
        if not all_ids:
            raise BenchmarkRunTestSelectionError(f"Bundle {name!r} has no tests in the database.")
        if tests_by_bundle is None or name not in tests_by_bundle:
            resolved[name] = list(all_ids)
            continue
        sel = tests_by_bundle[name]
        allowed = set(all_ids)
        bad = sorted(set(sel) - allowed)
        if bad:
            raise BenchmarkRunTestSelectionError(
                f"tests_by_bundle[{name!r}] contains test id(s) not in this bundle: {bad}"
            )
        resolved[name] = sorted(set(sel))
    return resolved


def _run_bundle_in_process(
    bundle_id: str,
    run_id: int,
    skip_alembic_upgrade: bool,
    llm_provider_id: Optional[int],
    llm_provider_model_id: Optional[int],
    llm_provider_model_config_id: Optional[int],
    custom_app_id: Optional[int],
    custom_app_config_id: Optional[int],
    test_ids: Optional[List[int]] = None,
) -> None:
    """
    Wrapper to run a bundle in a separate process.

    Instantiates BenchmarkExecutionService and calls execute_bundle on the DB-backed path.
    Used as the target for multiprocessing.Process (must be module-level to be picklable).

    The parent process must have run Alembic migrations on the same MOONSHOT_DB_PATH
    before starting this worker. When skip_alembic_upgrade is True, SessionManager
    will not run upgrade in this process (avoids races on shared SQLite).

    Args:
        bundle_id: Bundle identifier to execute
        run_id: benchmark_run.id for this run
        skip_alembic_upgrade: If True, skip Alembic in this process (set before any DB use).
        llm_provider_id / llm_provider_model_id / llm_provider_model_config_id: DB connector FKs (LLM path).
        custom_app_id / custom_app_config_id: DB connector FKs (Custom_App path).
        test_ids: Optional list of benchmark_test.id to run for this bundle (subset or full).
    """
    if skip_alembic_upgrade:
        set_skip_alembic_upgrade(True)
    try:
        execution_service = BenchmarkExecutionService()
        execution_service.execute_bundle(
            bundle_id,
            None,
            run_id=run_id,
            write_to_db=True,
            write_combined_results_file=False,
            llm_provider_id=llm_provider_id,
            llm_provider_model_id=llm_provider_model_id,
            llm_provider_model_config_id=llm_provider_model_config_id,
            custom_app_id=custom_app_id,
            custom_app_config_id=custom_app_config_id,
            test_ids=test_ids,
        )
    finally:
        if skip_alembic_upgrade:
            set_skip_alembic_upgrade(False)


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
        run_id: int,
        llm_provider_id: Optional[int] = None,
        llm_provider_model_id: Optional[int] = None,
        llm_provider_model_config_id: Optional[int] = None,
        custom_app_id: Optional[int] = None,
        custom_app_config_id: Optional[int] = None,
        test_ids: Optional[List[int]] = None,
    ) -> str:
        """
        Validate the bundle (DB only), start its execution in a daemon process, and return the bundle id.

        Resolves the bundle from the DB only (seeded config). Callers can map the returned
        bundle_id to a response DTO. Raises KeyError if the bundle is not found in the DB.

        Args:
            bundle_name: Bundle system name from the request (used to resolve the bundle in DB)
            run_id: benchmark_run.id for the background process.
            llm_provider_id / llm_provider_model_id / llm_provider_model_config_id: DB-backed connector FKs (LLM path).
            custom_app_id / custom_app_config_id: DB-backed connector FKs (Custom_App path).
            test_ids: When set, only these benchmark_test.id values are executed for the bundle.

        Returns:
            The resolved bundle id (same as bundle_name).

        Raises:
            KeyError: If the bundle is not found in the DB.
        """
        config_adapter = BenchmarkTestConfigAdapter()
        try:
            config_adapter.get_bundle_id_by_system_name_latest(bundle_name)
        except ValueError:
            logger.error("Bundle with ID %r not found in DB. Seed bundles first.", bundle_name)
            raise KeyError(f"Bundle with ID '{bundle_name}' not found") from None

        process = multiprocessing.Process(
            target=_run_bundle_in_process,
            args=(
                bundle_name,
                run_id,
                True,
                llm_provider_id,
                llm_provider_model_id,
                llm_provider_model_config_id,
                custom_app_id,
                custom_app_config_id,
                test_ids,
            ),
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
        llm_provider_id: Optional[int] = None,
        llm_provider_model_id: Optional[int] = None,
        llm_provider_model_config_id: Optional[int] = None,
        custom_app_id: Optional[int] = None,
        custom_app_config_id: Optional[int] = None,
        tests_by_bundle: Optional[Dict[str, List[int]]] = None,
    ) -> None:
        """
        Start a benchmark run: create a benchmark run entity, then execute multiple bundles
        in separate daemon processes, passing the run id for them to use.

        Uses relational llm_provider / llm_provider_model / llm_provider_model_config ids
        or custom_app / custom_app_config ids for benchmark execution.

        Args:
            run_name: Name for this benchmark run.
            bundle_names: Names/ids of the bundles to execute.
            llm_provider_id: FK llm_provider.id (LLM path).
            llm_provider_model_id: FK llm_provider_model.id (LLM path).
            llm_provider_model_config_id: FK llm_provider_model_config.id (LLM path).
            custom_app_id: FK custom_app.id (Custom_App path).
            custom_app_config_id: FK custom_app_config.id (Custom_App path).
            tests_by_bundle: Optional map bundle system_name -> benchmark_test.id list (subset per bundle).

        Raises:
            KeyError: If any bundle is not found.
            BenchmarkRunTestSelectionError: If tests_by_bundle references ids not in a bundle.
            DatabaseConnectorConfigError: If LLM DB connector resolution fails.
            DatabaseCustomAppConnectorConfigError: If custom app connector resolution fails.
        """
        use_llm = (
            llm_provider_id is not None
            and llm_provider_model_id is not None
            and llm_provider_model_config_id is not None
        )
        use_custom_app = (
            custom_app_id is not None and custom_app_config_id is not None
        )

        if use_llm:
            DatabaseConnectorConfigService().build_connector_entity(
                llm_provider_id=llm_provider_id,
                llm_provider_model_id=llm_provider_model_id,
                llm_provider_model_config_id=llm_provider_model_config_id,
            )
            endpoint_type = "LLM_Provider"
        elif use_custom_app:
            DatabaseCustomAppConnectorConfigService().build_connector_entity(
                custom_app_id=custom_app_id,
                custom_app_config_id=custom_app_config_id,
            )
            endpoint_type = "Custom_App"
        else:
            raise ValueError(
                "Provide either LLM provider ids or custom app ids to start a benchmark run."
            )

        config_adapter = BenchmarkTestConfigAdapter()
        resolved_test_ids = _bundle_names_to_resolved_test_ids(
            bundle_names, tests_by_bundle, config_adapter
        )

        logger.info(
            "[BenchmarkExecutionService] Starting benchmark run: run_name=%s, "
            "endpoint_type=%s, llm_provider_id=%s, llm_provider_model_id=%s, "
            "llm_provider_model_config_id=%s, custom_app_id=%s, custom_app_config_id=%s, "
            "bundles=%s, tests_by_bundle=%s",
            run_name,
            endpoint_type,
            llm_provider_id,
            llm_provider_model_id,
            llm_provider_model_config_id,
            custom_app_id,
            custom_app_config_id,
            bundle_names,
            tests_by_bundle,
        )

        run_entity = BenchmarkRunEntity(
            name=run_name,
            status="running",
            endpoint_type=endpoint_type,
            start_time=datetime.now(timezone.utc),
            llm_provider_id=llm_provider_id,
            llm_provider_model_id=llm_provider_model_id,
            llm_provider_model_config_id=llm_provider_model_config_id,
            custom_app_id=custom_app_id,
            custom_app_config_id=custom_app_config_id,
        )
        saved_run = BenchmarkRunService().save_run(run_entity)
        run_id = saved_run.id
        if run_id is None:
            raise RuntimeError("BenchmarkRunService.save_run did not return a persisted run id")

        pop_service = BenchmarkRunTestBundlePopulationService()

        for bundle_name in bundle_names:
            ids_for_bundle = resolved_test_ids[bundle_name]
            try:
                pop_service.populate_run_bundle(
                    run_id, bundle_name, test_ids=ids_for_bundle
                )
            except ValueError as e:
                logger.warning(
                    f"[BenchmarkExecutionService] Skipping populate_run_bundle for run_id={run_id}, "
                    f"bundle={bundle_name}: {e}"
                )
            self.start_bundle_in_background(
                bundle_name,
                run_id,
                llm_provider_id=llm_provider_id,
                llm_provider_model_id=llm_provider_model_id,
                llm_provider_model_config_id=llm_provider_model_config_id,
                custom_app_id=custom_app_id,
                custom_app_config_id=custom_app_config_id,
                test_ids=ids_for_bundle,
            )

    def execute_bundle(
        self,
        bundle_id: str,
        connector: Optional[str] = None,
        run_id: Optional[int] = None,
        write_to_db: bool = True,
        llm_provider_id: Optional[int] = None,
        llm_provider_model_id: Optional[int] = None,
        llm_provider_model_config_id: Optional[int] = None,
        custom_app_id: Optional[int] = None,
        custom_app_config_id: Optional[int] = None,
        write_combined_results_file: bool = True,
        test_ids: Optional[List[int]] = None,
    ) -> None:
        """
        Execute a bundle (multiple benchmark tests) synchronously and optionally write a combined results file.

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
            connector: YAML connector id when using legacy path (mutually exclusive with DB ids).
            run_id: Optional benchmark run id (from BenchmarkRunEntity). Required for DB path; if None on DB path, a run is created.
            llm_provider_id / llm_provider_model_id / llm_provider_model_config_id: When all set, build ConnectorEntity from LLM DB rows.
            custom_app_id / custom_app_config_id: When both set, build ConnectorEntity from custom app DB rows.
            write_to_db: If True (default), run_benchmark writes results to DB when run_test/prompts exist. If False, prompts come from dataset load and no DB write.
            write_combined_results_file: If True (default), write combined bundle JSON under MOONSHOT_BENCHMARK_RESULTS_DIR.
                Background workers for ``start_benchmark_run`` pass False so API runs persist only to the DB.
            test_ids: When set on the DB path, only these benchmark_test.id values are run (must be a subset of the bundle).
                Ignored for file-based bundles (a warning is logged if set).
        """
        try:
            logger.info(f"[BenchmarkExecutionService] Starting bundle execution for bundle: {bundle_id}")

            use_llm_connector = (
                llm_provider_id is not None
                and llm_provider_model_id is not None
                and llm_provider_model_config_id is not None
            )
            use_custom_app_connector = (
                custom_app_id is not None and custom_app_config_id is not None
            )
            db_connector_entity = None
            if use_llm_connector:
                db_connector_entity = DatabaseConnectorConfigService().build_connector_entity(
                    llm_provider_id=llm_provider_id,
                    llm_provider_model_id=llm_provider_model_id,
                    llm_provider_model_config_id=llm_provider_model_config_id,
                )
                bench_connector = ""
            elif use_custom_app_connector:
                db_connector_entity = DatabaseCustomAppConnectorConfigService().build_connector_entity(
                    custom_app_id=custom_app_id,
                    custom_app_config_id=custom_app_config_id,
                )
                bench_connector = ""
            elif connector is not None:
                bench_connector = connector
            else:
                logger.error(
                    "[BenchmarkExecutionService] execute_bundle requires connector, "
                    "LLM id trio, or custom app id pair"
                )
                return

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
                all_bundle_test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_db_id)
                if not all_bundle_test_ids:
                    raise ValueError(f"Bundle has no tests: {bundle_id!r}")
                if test_ids is not None:
                    allowed = set(all_bundle_test_ids)
                    unknown = set(test_ids) - allowed
                    if unknown:
                        raise ValueError(
                            f"test_ids contains id(s) not in bundle {bundle_id!r}: {sorted(unknown)}"
                        )
                    test_ids_to_run = sorted(set(test_ids))
                    if not test_ids_to_run:
                        raise ValueError(f"test_ids is empty after filtering for bundle {bundle_id!r}")
                else:
                    test_ids_to_run = list(all_bundle_test_ids)
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
                    for tid in test_ids_to_run:
                        setup_service.create_run_test_with_prompts(effective_run_id, tid)
                for tid in test_ids_to_run:
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
                            connector=bench_connector,
                            prompt_processor=prompt_processor,
                            callback_fn=None,
                            write_result=False,
                            write_to_db=write_to_db,
                            db_run_id=effective_run_id if write_to_db else None,
                            test_id=tid,
                            connector_entity=db_connector_entity,
                        )
                        results.append(result)
                    return results

                eval_results = asyncio.run(_run_all_db())
            else:
                # Look in file for bundle (benchmark source YAML); if found, run with file-based config.
                if test_ids is not None:
                    logger.warning(
                        "[BenchmarkExecutionService] execute_bundle: test_ids filter ignored "
                        "for file-based bundle %s",
                        bundle_id,
                    )
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
                                connector=bench_connector,
                                prompt_processor=prompt_processor,
                                callback_fn=None,
                                write_result=False,
                                write_to_db=write_to_db,
                                db_run_id=run_id if write_to_db else None,
                                test_id=1,  # Placeholder: file path does not create run_test/prompts per test
                                connector_entity=db_connector_entity,
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

            if write_combined_results_file:
                result_path = task_manager._store_results_to_local_path(bundle_id, final_results_str)
                if result_path:
                    logger.info(
                        f"[BenchmarkExecutionService] Bundle completed successfully for bundle: {bundle_id}. "
                        f"Results written to: {result_path}"
                    )
                else:
                    logger.error(
                        f"[BenchmarkExecutionService] Failed to write results file for bundle: {bundle_id}"
                    )
            else:
                logger.info(
                    f"[BenchmarkExecutionService] Bundle completed successfully for bundle: {bundle_id}. "
                    "Combined results file skipped (persisted via DB when write_to_db is enabled)."
                )

            # When all run-test statuses for this run are completed, mark the benchmark run as completed.
            if use_db_path and effective_run_id is not None:
                status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
                run_statuses = status_repo.get_all_by_run_id(effective_run_id)
                if run_statuses and all(s.status == "completed" for s in run_statuses):
                    run_service = BenchmarkRunService()
                    run_entity = run_service.get_run_by_id(effective_run_id)
                    if run_entity is not None and run_entity.status == "running":
                        run_entity.status = "completed"
                        run_entity.end_time = datetime.now(timezone.utc)
                        run_service.update_run(run_entity)
                        logger.info(
                            f"[BenchmarkExecutionService] Benchmark run {effective_run_id} marked as completed."
                        )

        except Exception as e:
            logger.error(
                f"[BenchmarkExecutionService] Error executing bundle for bundle {bundle_id}: {str(e)}",
                exc_info=True,
            )
            # Don't re-raise the exception - background tasks should log errors but not crash
