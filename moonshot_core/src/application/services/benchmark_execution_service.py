"""
Service for executing benchmarks asynchronously.

This service handles the execution of benchmark tasks using TaskManager,
providing a clean interface for background task execution.
"""

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
            
            # Convert metric string to dict format 
            metric_dict = {"name": metric}
            
            # Auto-generate run_id using timestamp format
            run_id = test_name
            logger.info(f"[BenchmarkExecutionService] Generated run_id: {run_id}")
            
            # Use default prompt processor
            prompt_processor = "asyncio_prompt_processor_adapter"
            
            # Create TaskManager instance
            task_manager = TaskManager()
            
            # Execute the benchmark
            logger.info(
                f"[BenchmarkExecutionService] Executing benchmark with parameters: "
                f"test_name={test_name}, dataset={dataset}, metric={metric}, connector={connector}"
            )
            
            result_path = await task_manager.run_benchmark(
                run_id=run_id,
                test_name=test_name,
                dataset=dataset,
                metric=metric_dict,
                connector=connector,
                prompt_processor=prompt_processor,
                callback_fn=None,
                write_result=True,
            )
            
            if result_path:
                logger.info(
                    f"[BenchmarkExecutionService] Benchmark completed successfully for test: {test_name}. "
                    f"Results written to: {result_path}"
                )
            else:
                logger.warning(
                    f"[BenchmarkExecutionService] Benchmark completed but no result file was created "
                    f"for test: {test_name}"
                )
                
        except Exception as e:
            logger.error(
                f"[BenchmarkExecutionService] Error executing benchmark for test {test_name}: {str(e)}",
                exc_info=True
            )
            # Don't re-raise the exception - background tasks should log errors but not crash
