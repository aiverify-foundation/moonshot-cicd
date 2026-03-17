from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RunBundleRequestDTO(BaseModel):
    """
    RunBundleRequestDTO represents the data transfer object for bundle execution request.
    
    This DTO contains only the essential data fields for transferring bundle execution
    request information between different layers of the application, without complex logic.

    Attributes:
        bundle_name (str): The name of the bundle to execute.
        connector (str): The connector identifier to use for the bundle.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # The name of the bundle to execute
    bundle_name: str

    # The connector identifier to use for the bundle
    connector: str


class RunBundleResponseDTO(BaseModel):
    """
    RunBundleResponseDTO represents the data transfer object for bundle execution response.
    
    This DTO contains only the essential data fields for transferring bundle execution
    response information between different layers of the application, without complex logic.

    Attributes:
        bundle_name (str): The name of the bundle that was executed.
        message (str): A message describing the result of the bundle execution.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # The name of the bundle that was executed
    bundle_name: str

    # A message describing the result of the bundle execution
    message: str


class StartBenchmarkRunRequestDTO(BaseModel):
    """
    StartBenchmarkRunRequestDTO represents the request for starting a benchmark run
    (one or more bundles with a single run name and LLM config).

    Attributes:
        bundle_names (List[str]): Names/ids of the bundles to execute.
        run_name (str): Name for this benchmark run.
        llm_provider_name (str): Name of the LLM provider to use.
        llm_provider_config_name (str): Name of the LLM provider config to use (connector id).
    """

    bundle_names: List[str]
    run_name: str
    llm_provider_name: str
    llm_provider_config_name: str


class StartBenchmarkRunResponseDTO(BaseModel):
    """
    StartBenchmarkRunResponseDTO represents the response after starting a benchmark run.

    Attributes:
        message (str): A message indicating that the benchmark run has started successfully.
    """

    message: str


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
