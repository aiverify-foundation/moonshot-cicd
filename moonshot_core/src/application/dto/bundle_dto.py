from typing import List

from pydantic import BaseModel

from application.dto.benchmark_test_dto import BenchmarkTestDTO


class BundleDTO(BaseModel):
    """
    BundleDTO represents the data transfer object for a bundle of tests.
    
    This DTO contains only the essential data fields for transferring bundle
    information between different layers of the application, without complex logic.

    Attributes:
        name (str): The name of bundle.
        description (str): The description of bundle.
        tests (List[BenchmarkTestDTO]): The tests in the bundle.
        prompt_count (int): The total number of prompts across all tests in the bundle.
    """

    class Config:
        arbitrary_types_allowed = True

    # Name of the bundle
    name: str

    # Description of the bundle
    description: str = ""

    # List of test DTOs in the bundle
    tests: List[BenchmarkTestDTO] = []

    # Total number of prompts across all tests in the bundle
    prompt_count: int = 0

    def __str__(self) -> str:
        """String representation for debugging."""
        tests_info = ""
        if self.tests:
            tests_info = "  tests:\n"
            for i, test in enumerate(self.tests):
                # Indent each test's string representation
                test_str = str(test).replace('\n', '\n    ')
                tests_info += f"    [{i}] {test_str}\n"
        else:
            tests_info = "  tests: No tests\n"
        
        return (
            f"BundleDTO(\n"
            f"  name: '{self.name}'\n"
            f"  description: '{self.description[:100]}{'...' if len(self.description) > 100 else ''}'\n"
            f"  prompt_count: {self.prompt_count}\n"
            f"{tests_info}"
            f")"
        )
