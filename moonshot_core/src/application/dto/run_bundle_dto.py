from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


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
        tests_by_bundle (Optional[Dict[str, List[int]]]): Optional map of bundle system_name
            to benchmark_test.id values to run for that bundle only. Keys must be a subset of
            bundle_names; omit a bundle to run all its tests. Each list must be non-empty when present.
    """

    bundle_names: List[str]
    run_name: str
    llm_provider_id: int
    llm_provider_model_id: int
    llm_provider_model_config_id: int
    tests_by_bundle: Optional[Dict[str, List[int]]] = None

    @model_validator(mode="after")
    def validate_tests_by_bundle_keys(self) -> "StartBenchmarkRunRequestDTO":
        if self.tests_by_bundle is None:
            return self
        bundle_set = set(self.bundle_names)
        for key, ids in self.tests_by_bundle.items():
            if key not in bundle_set:
                raise ValueError(
                    f"tests_by_bundle key {key!r} is not in bundle_names; "
                    "keys must only reference bundles included in this run."
                )
            if len(ids) == 0:
                raise ValueError(
                    f"tests_by_bundle[{key!r}] must not be an empty list when provided."
                )
        return self


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

    Returned by GET /api/benchmark-runs/{run_id}/prompts and GET .../results.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    run_test_id: int
    #: benchmark_test.id for the run-test this prompt belongs to (API-enriched).
    test_id: Optional[int] = None
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


class PatchBenchmarkRunTestPromptUserDTO(BaseModel):
    """
    Request body for PATCH user feedback (verdict and notes) on a benchmark run test prompt.

    The client may send both fields on each update; null user_evaluation clears the stored verdict.
    """

    user_evaluation: Optional[int] = None
    user_notes: Optional[str] = None


class BenchmarkRunResultsBundleSummaryDTO(BaseModel):
    """
    One logical bundle in a run: metadata plus test ids linked via benchmark_run_test_bundle.

    ``margin_of_error`` is the half-width of the 95% t-based interval on the mean of
    per-test scores (mean ``evaluation_accuracy`` per test in this bundle). For bundles
    with two or fewer tests it is always ``0.0``.
    ``None`` when there are more than two tests but no scored tests contribute (same scale as scores).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    test_bundle_id: int
    name: str
    system_name: str
    test_ids: List[int]
    margin_of_error: Optional[float] = None


class BenchmarkRunResultsResponseDTO(BaseModel):
    """
    Full results payload for the results UI: run header, bundle summaries, all prompts with test_id.

    Returned by GET /api/benchmark-runs/{run_id}/results.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run: BenchmarkRunResponseDTO
    bundles: List[BenchmarkRunResultsBundleSummaryDTO]
    prompts: List[BenchmarkRunTestPromptResponseDTO]
