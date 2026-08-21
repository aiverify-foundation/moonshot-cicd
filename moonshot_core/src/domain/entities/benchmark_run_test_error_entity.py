from typing import Optional

from pydantic import BaseModel, ConfigDict


class BenchmarkRunTestErrorEntity(BaseModel):
    """
    Domain entity for a benchmark run test prompt error record.

    Mirrors the benchmark_run_test_error table (error_message per prompt row).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    benchmark_run_test_prompt_id: int
    error_message: str
    error_source: str
