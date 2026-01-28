"""
Service for executing benchmarks.

This service handles the execution of benchmark tasks using TaskManager,
providing a clean interface for background task execution.
Internally handles async operations while providing a synchronous interface.
"""

import json
import asyncio
from datetime import datetime
from domain.services.logger import configure_logger
from domain.services.task_manager import TaskManager

# Initialize logger for this module
logger = configure_logger(__name__)


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
    
    def execute_bundle(self, bundle_id: str, connector: str) -> None:
        """
        Execute a bundle (multiple benchmark tests) synchronously and write a combined results file.

        This follows the same combined JSON pattern as TaskManager.run_test:
        - run_metadata: run_id/test_id/start/end/duration
        - run_results: list of benchmark JSON results (one per test)

        Args:
            bundle_id: Bundle identifier to load (via BenchmarkService.get_bundle_by_id)
            connector: Connector name to use for all tests in the bundle
        """
        try:
            logger.info(f"[BenchmarkExecutionService] Starting bundle execution for bundle: {bundle_id}")

            # Lazy import to avoid heavy imports at module load and keep parity with api process execution
            from application.services.benchmark import BenchmarkService  # noqa: WPS433

            # Record the start time of the bundle
            start_time = datetime.now()

            benchmark_service = BenchmarkService(None, None)
            bundle = benchmark_service.get_bundle_by_id(bundle_id)

            # Use default prompt processor
            prompt_processor = "asyncio_prompt_processor_adapter"

            task_manager = TaskManager()

            async def _run_all() -> list[str]:
                tasks = []
                for test in bundle.tests:
                    tasks.append(
                        task_manager.run_benchmark(
                            run_id=bundle_id,
                            test_name=test.id,
                            dataset=test.dataset.id if test.dataset else "",
                            metric=test.metric,
                            connector=connector,
                            prompt_processor=prompt_processor,
                            callback_fn=None,
                            write_result=False,
                            write_to_db=True,
                        )
                    )
                return await asyncio.gather(*tasks)

            eval_results = asyncio.run(_run_all())

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

            run_metadata = {
                "run_metadata": {
                    "run_id": bundle_id,
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
