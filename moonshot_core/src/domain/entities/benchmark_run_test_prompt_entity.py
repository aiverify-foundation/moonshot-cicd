from typing import Optional

from pydantic import BaseModel, ConfigDict


class BenchmarkRunTestPromptEntity(BaseModel):
    """
    Domain entity for a single benchmark run test prompt (per-prompt result within a run-test).

    Mirrors the benchmark_run_test_prompt table: target, prediction, evaluation, user_notes.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None  # None or 0 when creating new; set after save
    run_test_id: int
    prompt_id: int
    status: str
    target: str = ""

    # Optional / nullable in DB
    prompt_additional_info: Optional[str] = None
    prediction_result: Optional[str] = None
    prediction_context: Optional[str] = None
    evaluation_prompt: Optional[str] = None
    evaluation_prediction_result: Optional[str] = None
    evaluation_accuracy: Optional[float] = None
    user_evaluation: Optional[int] = None
    user_notes: Optional[str] = None
