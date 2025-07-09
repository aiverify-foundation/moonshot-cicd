from typing import Annotated, Any, Optional, Union

from pydantic import BaseModel, Field


class IndividualResult(BaseModel):
    prompt_id: int
    prompt: str
    predicted_result: dict
    target: str
    evaluated_result: dict
    prompt_additional_info: dict
    state: str


class RunResults(BaseModel):
    individual_results: dict[str, list[IndividualResult]] = Field(min_length=1)
    evaluation_summary: dict = Field(min_length=1)


class RunMetadata(BaseModel):
    test_name: str
    dataset: Optional[str] = None
    metric: dict
    type: str
    connector: dict
    start_time: str
    end_time: str
    duration: float
    attack_module: Optional[dict] = None


class RunResultEntry(BaseModel):
    metadata: RunMetadata
    results: RunResults


class RunMetaData(BaseModel):
    run_id: str
    test_id: str
    start_time: str
    end_time: str
    duration: float


class Schema1(BaseModel):
    run_metadata: RunMetaData
    run_results: Annotated[list["RunResultEntry"], Field(min_length=1)]


def extract_ga_report_info(
    data: dict[str, Any],
) -> dict[str, Union[str, dict, list]]:
    """
    Extracts and processes report information from a Moonshot GA test result structure.

    This function analyzes test results data to generate a summary report. It processes each test run
    to determine success/failure status, compiles evaluation metrics, and extracts key metadata.
    The function handles both successful and failed test cases, tracking counts for reporting.

    Args:
        data (dict[str, Any]): The test results data structure containing:
            - run_metadata: Overall test run information including timing and identifiers
            - run_results: Array of test results, each containing:
                - metadata: Test configuration and run details
                - results: Test outcomes and evaluation metrics

    Returns:
        dict[str, Union[str, dict, list]]: A processed report with:
            - status: Overall run status ("completed"/"incomplete")
            - total_tests: Test outcome statistics:
                - test_success: Count of tests with valid evaluation summaries
                - test_fail: Count of tests missing evaluation data
                - test_skip: Count of skipped tests (always 0 in current implementation)
            - evaluation_summaries_and_metadata: Array of test summaries containing:
                - test_name: Identifier for the test
                - id: Test identifier (matches test_name)
                - model_id: Identifier for the model used in testing
                - summary: Detailed evaluation metrics and results
    """
    # Track test outcomes for reporting
    test_success = 0
    test_fail = 0
    test_skip = 0  # Reserved for future use - currently always 0

    # Calculate total tests and determine overall completion status
    total_tests = len(data.get("run_results", []))
    status = "completed" if total_tests > 0 else "incomplete"

    evaluation_summaries_and_metadata = []
    for result in data.get("run_results", []):
        meta_data = result.get("metadata", {})
        test_name = meta_data.get("test_name", "Unnamed Test")
        model_id = meta_data.get("connector", {}).get("model", "Unknown Model")
        summary = result.get("results", {}).get("evaluation_summary", {})

        # Increment success/fail counters based on evaluation summary presence
        if summary:
            test_success += 1
        else:
            test_fail += 1

        evaluation_summaries_and_metadata.append(
            {
                "test_name": test_name,
                "id": test_name,
                "model_id": model_id,
                "summary": summary,
            }
        )

    return {
        "status": status,
        "total_tests": {
            "test_success": test_success,
            "test_fail": test_fail,
            "test_skip": test_skip,
        },
        "evaluation_summaries_and_metadata": evaluation_summaries_and_metadata,
    }
