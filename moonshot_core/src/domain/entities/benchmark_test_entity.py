from typing import Dict, Optional

from pydantic import BaseModel

from domain.services.enums.test_types import TestTypes
from domain.entities.dataset_entity import DatasetEntity


class BenchmarkTestEntity(BaseModel):
    """
    TestConfigEntity represents the configuration for a test case.

    Attributes:
        name (str): The name of the test configuration.
        type (TestTypes): The type of the test configuration (can be Benchmark or Scan).
        attack_module (dict): The module used for attack simulations, including parameters.
        metric (str): The metric used to evaluate the test.
        dataset (str): The dataset used for benchmark.
        prompt (str): The prompt or scenario description for the test.
    """

    class Config:
        arbitrary_types_allowed = True

    id: str

    # Name of the test
    name: str

    # Data used for benchmark
    dataset: Optional[DatasetEntity] = None

    # Metric used to evaluate the test
    metric: dict

    # Test description
    description: str = ""

    def get_prompt_count(self) -> int:
        if self.dataset:
            return self.dataset.num_of_dataset_prompts
        else:
            return 0
