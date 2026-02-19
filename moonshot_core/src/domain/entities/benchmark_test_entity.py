from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from domain.services.enums.test_types import TestTypes
from domain.entities.dataset_entity import DatasetEntity


class BenchmarkTestEntity(BaseModel):
    """
    BenchmarkTestEntity represents the configuration for a benchmark test case.

    This entity defines the structure for benchmark test configurations, including
    the dataset to be used, evaluation metrics, and test metadata.

    Attributes:
        id (str): Unique identifier for the benchmark test.
        name (str): The name of the benchmark test configuration.
        dataset (Optional[DatasetEntity]): The dataset entity used for the benchmark.
        metric (dict): The metric configuration used to evaluate the test.
        description (str): The description or scenario for the benchmark test.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
