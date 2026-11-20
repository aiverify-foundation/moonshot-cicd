from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BenchmarkRunTestPromptMetricReasoningEntity(BaseModel):
    """
    Domain entity for metric reasoning on one benchmark run test prompt.

    This is reasoning produced by the metric (the evaluator), not the tested
    model's reasoning. Rows are append-only: re-evaluation inserts a new row.
    The current reasoning for a prompt is the row with the highest id.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    benchmark_run_test_prompt_id: int
    reasoning: str
    create_dt: Optional[datetime] = None
