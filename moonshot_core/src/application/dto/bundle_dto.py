from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from application.dto.benchmark_test_dto import BenchmarkTestDTO


class BundleDTO(BaseModel):
    """
    BundleDTO represents the data transfer object for a bundle of tests.

    This DTO contains only the essential data fields for transferring bundle
    information between different layers of the application, without complex logic.

    Attributes:
        id (str): Unique identifier for the bundle.
        name (str): The name of bundle.
        description (str): The description of bundle.
        category (str): The category of bundle.
        tests (List[BenchmarkTestDTO]): The tests in the bundle.
        prompt_count (int): The total number of prompts across all tests in the bundle.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Unique identifier for the bundle
    id: str = ""

    # Name of the bundle
    name: str

    # Description of the bundle
    description: str = ""

    # Category of the bundle
    category: str = ""

    # List of test DTOs in the bundle
    tests: List[BenchmarkTestDTO] = []

    # Total number of prompts across all tests in the bundle
    prompt_count: int = 0

    #: Aggregated prompt-level rows from test_details.csv for all datasets in this bundle.
    details: Optional[list[dict[str, str]]] = None
