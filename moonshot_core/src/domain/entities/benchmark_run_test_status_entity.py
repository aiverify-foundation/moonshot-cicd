from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BenchmarkRunTestStatusEntity(BaseModel):
    """
    Domain entity for the status of a single test within a benchmark run.

    Mirrors the benchmark_run_test_status table
    (not_started, in_progress, completed, pause, skipped).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    run_id: int
    test_id: int
    status: str
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    connector_pre_prompt: Optional[str] = None
    connector_post_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
