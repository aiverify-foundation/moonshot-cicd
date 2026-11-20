"""DTOs for metric binary score result labels."""

from pydantic import BaseModel, Field


class MetricScoreResultNamesDTO(BaseModel):
    """Pass/fail result names owned by a metric adapter."""

    metric_name: str = Field(..., description="Metric adapter module name")
    result_pass: str = Field(
        ..., description="Label for score 1 (RESULT_PASS)"
    )
    result_fail: str = Field(
        ..., description="Label for score 0 (RESULT_FAIL)"
    )
