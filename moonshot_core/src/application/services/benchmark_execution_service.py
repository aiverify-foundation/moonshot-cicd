"""
Service for executing benchmarks asynchronously.

This service handles the execution of benchmark tasks using TaskManager,
providing a clean interface for background task execution.
"""

import json
from datetime import datetime
from domain.services.logger import configure_logger
from domain.services.task_manager import TaskManager

# Initialize logger for this module
logger = configure_logger(__name__)


class BenchmarkExecutionService:
    """
    Service class for executing benchmark tasks asynchronously.
    
    This service provides methods to execute benchmarks in the background,
    handling TaskManager initialization, parameter conversion, and error handling.
    """
    
    def __init__(self):
        """Initialize the BenchmarkExecutionService."""
        logger.info("[BenchmarkExecutionService] Initializing BenchmarkExecutionService")
    
    async def execute_benchmark(
        self,
        test_name: str,
        dataset: str,
        metric: str,
        connector: str
    ) -> None:
        """
        Execute a benchmark asynchronously.
        
        This method converts the metric string to the required dict format,
        generates a run_id, and executes the benchmark using TaskManager.
        Results will be written to data/results/{run_id}.json when complete.
        
        Follows the same pattern as run_test: collects JSONs from run_benchmark
        and creates a combined JSON file with run_metadata and run_results.
        
        Args:
            test_name: Unique identifier for the benchmark test
            dataset: Dataset name to load
            metric: Metric name (e.g., "accuracy_adapter")
            connector: Connector name to use
            
        Raises:
            Exception: If benchmark execution fails (logged but not re-raised)
        """
        try:
            logger.info(f"[BenchmarkExecutionService] Starting benchmark execution for test: {test_name}")
            
            # Record the start time of the benchmark
            start_time = datetime.now()
            
            # Convert metric string to dict format 
            metric_dict = {"name": metric}
            
            # Auto-generate run_id using timestamp format
            run_id = test_name
            
            # Use default prompt processor
            prompt_processor = "asyncio_prompt_processor_adapter"
            
            # Create TaskManager instance
            task_manager = TaskManager()
            
            # Get JSON string from run_benchmark (with write_result=False, like run_test does)
            serialized_results = await task_manager.run_benchmark(
                run_id=run_id,
                test_name=test_name,
                dataset=dataset,
                metric=metric_dict,
                connector=connector,
                prompt_processor=prompt_processor,
                callback_fn=None,
                write_result=False,
            )
            
            # Record the end time and calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if serialized_results:
                try:
                    # Parse the JSON result from run_benchmark (like run_test does)
                    json_result = json.loads(serialized_results)
                    
                    # Create run_metadata structure (following run_test pattern)
                    run_metadata = {
                        "run_metadata": {
                            "run_id": run_id,
                            "test_id": test_name,
                            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "duration": duration,
                        }
                    }
                    
                    # Create run_results structure (following run_test pattern)
                    formatted_json_results = {"run_results": [json_result]}
                    
                    # Combine metadata and results (following run_test pattern)
                    final_results = run_metadata | formatted_json_results
                    final_results_str = json.dumps(final_results, indent=4)
                    
                    # Write to file using the same method as run_test
                    result_path = task_manager._store_results_to_local_path(run_id, final_results_str)
                    
                    if result_path:
                        logger.info(
                            f"[BenchmarkExecutionService] Benchmark completed successfully for test: {test_name}. "
                            f"Results written to: {result_path}"
                        )
                    else:
                        logger.error(
                            f"[BenchmarkExecutionService] Failed to write results file for test: {test_name}"
                        )
                except Exception as e:
                    logger.error(
                        f"[BenchmarkExecutionService] Error creating combined results JSON: {str(e)}",
                        exc_info=True
                    )
                    # Still log success since run_benchmark completed
                    logger.info(
                        f"[BenchmarkExecutionService] Benchmark completed for test: {test_name}"
                    )
            else:
                logger.warning(
                    f"[BenchmarkExecutionService] Benchmark completed but no result was returned "
                    f"for test: {test_name}"
                )
                
        except Exception as e:
            logger.error(
                f"[BenchmarkExecutionService] Error executing benchmark for test {test_name}: {str(e)}",
                exc_info=True
            )
            # Don't re-raise the exception - background tasks should log errors but not crash
