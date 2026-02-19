from asyncio import streams
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from domain.entities.benchmark_test_entity import BenchmarkTestEntity

class TestBundleEntity(BaseModel):
    """
    TestBundleEntity represents the configuration for a bundle of benchmark tests.

    This entity groups multiple benchmark tests together, providing organization
    and categorization for related test configurations.

    Attributes:
        id (str): Unique identifier for the bundle.
        name (str): The name of the bundle.
        description (str): The description of the bundle.
        category (str): The category classification for the bundle.
        tests (List[BenchmarkTestEntity]): List of benchmark test entities in the bundle.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Name of the bundle
    name: str

    # Description of the bundle
    description: str = ""

    # List of test names in the bundle
    tests: List[BenchmarkTestEntity] = []

    category: str = ""

    id: str = ""

    def get_prompt_count(self) -> int:
        return sum(test.get_prompt_count() for test in self.tests)