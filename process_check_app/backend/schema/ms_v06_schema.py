from typing import Annotated, Any, Optional, Union

from pydantic import BaseModel, Field


class RecipeDetail(BaseModel):
    model_id: str
    dataset_id: str
    prompt_template_id: str
    data: Annotated[list[dict], Field(min_length=1)]
    metrics: Annotated[list[dict], Field(min_length=1)]


class Recipe(BaseModel):
    id: str
    details: Annotated[list["RecipeDetail"], Field(min_length=1)]
    evaluation_summary: Annotated[list[dict], Field(min_length=1)]
    grading_scale: dict
    total_num_of_prompts: int


class Cookbook(BaseModel):
    id: str
    recipes: Annotated[list[Recipe], Field(min_length=1)]
    overall_evaluation_summary: Annotated[list[dict], Field(min_length=1)]
    total_num_of_prompts: int


class Results(BaseModel):
    cookbooks: Annotated[list[Cookbook], Field(min_length=1)]


class MetaData(BaseModel):
    id: str
    start_time: str
    end_time: str
    duration: int
    status: str
    recipes: Optional[Any] = None
    cookbooks: Annotated[list[str], Field(min_length=1)]
    endpoints: Annotated[list[str], Field(min_length=1)]
    prompt_selection_percentage: int
    random_seed: int
    system_prompt: str


class Schema2(BaseModel):
    metadata: MetaData
    results: Results


def extract_06_report_info(
    report_json: dict[str, Any],
) -> dict[str, Union[str, dict, list]]:
    """
    Extracts report information from a Moonshot v0.6 Result Structure.

    This function processes the provided report JSON to extract key metrics and information from test runs.
    It calculates test success/failure counts, determines overall status, and compiles evaluation
    summaries with relevant metadata for each recipe in the cookbooks.

    Args:
        report_json (dict[str, Any]): Raw test results data containing:
            - metadata: Information about the overall test run including status
            - results: Dictionary containing list of cookbooks with recipes and their evaluation summaries

    Returns:
        dict[str, Union[str, dict, list]]: Processed report containing:
            - status: Status from metadata, defaults to "Unknown" if not found
            - total_tests: Count breakdown of test outcomes:
                - test_success: Number of recipes with evaluation summaries
                - test_fail: Number of recipes without evaluation summaries
                - test_skip: Number of skipped recipes (currently always 0)
            - evaluation_summaries_and_metadata: List of recipe result summaries, each containing:
                - test_name: Name of the recipe
                - id: Recipe identifier
                - summary: Evaluation metrics including:
                    - avg_grade_value: Rounded average grade value
                    - grade: Letter grade or "N/A"
    """
    # Extract status from metadata
    status = report_json.get("metadata", {}).get("status", "Unknown")

    # Initialize test counts
    test_success = 0
    test_fail = 0
    test_skip = 0  # Default to 0 as instructed

    cookbooks = report_json.get("results", {}).get("cookbooks", [])
    # Gather unique evaluation summaries (optional field)
    evaluation_summaries = []
    seen_test_names = set()

    for cookbook in cookbooks:
        recipes = cookbook.get("recipes", [])
        for recipe in recipes:
            test_name = recipe.get("id", "Unnamed Recipe")
            if test_name in seen_test_names:
                continue  # Skip if we've already processed this test name

            summaries = recipe.get("evaluation_summary")
            if summaries:
                test_success += 1
                summary = summaries[
                    0
                ]  # Assuming you want the first summary for each test
                summary_with_id = {
                    "test_name": test_name,
                    "id": recipe.get("id"),
                    "summary": {
                        "avg_grade_value": round(
                            summary.get("avg_grade_value", 0.0), 2
                        ),
                        "grade": summary.get("grade", "N/A"),
                    },
                }
                evaluation_summaries.append(summary_with_id)
                seen_test_names.add(test_name)  # Mark this test name as seen
            else:
                test_fail += 1

    return {
        "status": status,
        "total_tests": {
            "test_success": test_success,
            "test_fail": test_fail,
            "test_skip": test_skip,
        },
        "evaluation_summaries_and_metadata": evaluation_summaries,
    }
