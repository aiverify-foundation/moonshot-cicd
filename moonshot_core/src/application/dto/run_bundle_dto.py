from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class StartBenchmarkRunRequestDTO(BaseModel):
    """
    StartBenchmarkRunRequestDTO represents the request for starting a benchmark run
    (one or more bundles with a single run name and relational LLM config).

    Attributes:
        bundle_names (List[str]): Names/ids of the bundles to execute.
        run_name (str): Name for this benchmark run.
        llm_provider_id (int): FK llm_provider.id
        llm_provider_model_id (int): FK llm_provider_model.id
        llm_provider_model_config_id (int): FK llm_provider_model_config.id
    """

    bundle_names: List[str]
    run_name: str
    llm_provider_id: int
    llm_provider_model_id: int
    llm_provider_model_config_id: int


class StartBenchmarkRunResponseDTO(BaseModel):
    """
    StartBenchmarkRunResponseDTO represents the response after starting a benchmark run.

    Attributes:
        message (str): A message indicating that the benchmark run has started successfully.
    """

    message: str


class BenchmarkRunResponseDTO(BaseModel):
    """
    Response DTO for a benchmark_run row.

    Returned by GET /api/benchmark-runs.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    name: str
    status: str
    endpoint_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    llm_provider_id: Optional[int] = None
    llm_provider_model_id: Optional[int] = None
    llm_provider_model_config_id: Optional[int] = None


class BenchmarkRunTestBundleResponseDTO(BaseModel):
    """
    Response DTO for a benchmark_run_test_bundle row (run ↔ bundle ↔ test link).

    Returned by GET /api/benchmark-runs/{run_id}/run-test-bundles.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    run_id: int
    test_bundle_id: int
    test_id: int


class BenchmarkRunTestPromptResponseDTO(BaseModel):
    """
    Response DTO for a single benchmark run test prompt (per-prompt result within a run-test).

    Returned by GET /api/benchmark-runs/{run_id}/prompts.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    run_test_id: int
    prompt_id: int
    status: str
    target: str = ""
    prompt_additional_info: Optional[str] = None
    prediction_result: Optional[str] = None
    prediction_context: Optional[str] = None
    evaluation_prompt: Optional[str] = None
    evaluation_prediction_result: Optional[str] = None
    evaluation_accuracy: Optional[float] = None
    user_evaluation: Optional[int] = None
    user_notes: Optional[str] = None
    #: benchmark_test.name (display name) for the run-test this prompt belongs to (API-enriched).
    test_name: str = ""
