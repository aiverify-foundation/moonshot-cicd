from datetime import datetime
import ast
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class StartBenchmarkRunRequestDTO(BaseModel):
    """
    StartBenchmarkRunRequestDTO represents the request for starting a benchmark run
    (one or more bundles with a single run name and relational LLM or custom app config).

    Attributes:
        bundle_names (List[str]): Names/ids of the bundles to execute.
        run_name (str): Name for this benchmark run.
        llm_provider_id (Optional[int]): FK llm_provider.id (LLM path).
        llm_provider_model_id (Optional[int]): FK llm_provider_model.id (LLM path).
        llm_provider_model_config_id (Optional[int]): FK llm_provider_model_config.id (LLM path).
        custom_app_id (Optional[int]): FK custom_app.id (Custom_App path).
        custom_app_config_id (Optional[int]): FK custom_app_config.id (Custom_App path).
        tests_by_bundle (Optional[Dict[str, List[int]]]): Optional map of bundle system_name
            to benchmark_test.id values to run for that bundle only. Keys must be a subset of
            bundle_names; omit a bundle to run all its tests. Each list must be non-empty when present.
    """

    bundle_names: List[str]
    run_name: str
    llm_provider_id: Optional[int] = None
    llm_provider_model_id: Optional[int] = None
    llm_provider_model_config_id: Optional[int] = None
    custom_app_id: Optional[int] = None
    custom_app_config_id: Optional[int] = None
    tests_by_bundle: Optional[Dict[str, List[int]]] = None

    @model_validator(mode="after")
    def validate_endpoint_ids(self) -> "StartBenchmarkRunRequestDTO":
        llm_set = (
            self.llm_provider_id is not None
            and self.llm_provider_model_id is not None
            and self.llm_provider_model_config_id is not None
        )
        llm_partial = (
            self.llm_provider_id is not None
            or self.llm_provider_model_id is not None
            or self.llm_provider_model_config_id is not None
        )
        custom_set = (
            self.custom_app_id is not None and self.custom_app_config_id is not None
        )
        custom_partial = (
            self.custom_app_id is not None or self.custom_app_config_id is not None
        )
        if llm_set and custom_partial:
            raise ValueError(
                "Provide either LLM provider ids or custom app ids, not both."
            )
        if custom_set and llm_partial:
            raise ValueError(
                "Provide either LLM provider ids or custom app ids, not both."
            )
        if not llm_set and not custom_set:
            raise ValueError(
                "Provide either all three LLM provider ids or both custom app ids."
            )
        if llm_partial and not llm_set:
            raise ValueError(
                "When using LLM provider endpoint, llm_provider_id, "
                "llm_provider_model_id, and llm_provider_model_config_id are all required."
            )
        if custom_partial and not custom_set:
            raise ValueError(
                "When using Custom_App endpoint, custom_app_id and "
                "custom_app_config_id are both required."
            )
        return self

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


class CheckBenchmarkRunNameResponseDTO(BaseModel):
    """
    Response DTO for benchmark run name availability check.

    Returned by GET /api/benchmark-runs/check-name.
    """

    run_name: str
    available: bool


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
    custom_app_id: Optional[int] = None
    custom_app_config_id: Optional[int] = None


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


def score_from_evaluation_prediction_result(raw: Optional[str]) -> Optional[float]:
    """
    Read numeric score from ``evaluation_prediction_result`` only (never from
    ``evaluation_accuracy``).

    Accepts: JSON object with a ``score`` key; JSON number; or a Python ``repr`` of a dict
    or number, as written by ``str(evaluated_result)`` for metric outputs.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    parsed: Any
    try:
        parsed = json.loads(s)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(s)
        except (ValueError, SyntaxError):
            return None
    if isinstance(parsed, bool):
        return None
    if isinstance(parsed, (int, float)):
        return float(parsed)
    if not isinstance(parsed, dict):
        return None
    val = parsed.get("score")
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    return None


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

    @computed_field
    @property
    def score(self) -> Optional[float]:
        """Numeric score parsed only from ``evaluation_prediction_result`` (see ``score_from_evaluation_prediction_result``)."""
        return score_from_evaluation_prediction_result(self.evaluation_prediction_result)


class PatchBenchmarkRunTestPromptUserDTO(BaseModel):
    """
    Request body for PATCH user feedback (verdict and notes) on a benchmark run test prompt.

    The client may send both fields on each update; null user_evaluation clears the stored verdict.
    """

    user_evaluation: Optional[int] = None
    user_notes: Optional[str] = None


class BenchmarkRunTestMarginOfErrorDTO(BaseModel):
    """
    Half-width of the t-based interval on the mean prompt ``score`` for one ``benchmark_test``.

    Returned on GET .../results; one row per ``test_id`` that appears on at least one prompt
    in the run.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    test_id: int
    margin_of_error: float


class BenchmarkRunResultsBundleSummaryDTO(BaseModel):
    """
    One logical bundle in a run: metadata plus test ids linked via benchmark_run_test_bundle.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    test_bundle_id: int
    name: str
    system_name: str
    test_ids: List[int]


class BenchmarkRunResultsResponseDTO(BaseModel):
    """
    Full results payload for the results UI: run header, bundle summaries, all prompts with test_id.

    ``test_margin_of_error`` lists one row per ``benchmark_test.id`` that appears on any prompt
    in the run: ``margin_of_error`` is the half-width of the 95% t-interval on the mean of
    per-prompt ``score`` for that test (``0.0`` when the test has two or fewer scored prompts).

    Returned by GET /api/benchmark-runs/{run_id}/results.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run: BenchmarkRunResponseDTO
    bundles: List[BenchmarkRunResultsBundleSummaryDTO]
    prompts: List[BenchmarkRunTestPromptResponseDTO]
    test_margin_of_error: List[BenchmarkRunTestMarginOfErrorDTO] = Field(
        default_factory=list
    )
