from asyncio import streams
from typing import List, Optional

from pydantic import BaseModel

from domain.entities.benchmark_test_entity import BenchmarkTestEntity

class TestBundleEntity(BaseModel):
    """
    TestBundleEntity represents the configuration for a bundle of tests.

    Attributes:
        name (str): The name of bundle.
        description (str): The description of bundle.
        tests (list of strings): The tests in the bundle.
        num_of_bundle_prompts (int): The number of prompts in the bundle.
        num_of_recipes (int): The number of recipes in the bundle.
    """

    class Config:
        arbitrary_types_allowed = True

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