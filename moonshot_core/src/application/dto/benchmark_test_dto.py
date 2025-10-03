from typing import Dict, Optional

from pydantic import BaseModel

from application.dto.dataset_dto import DatasetDTO


class BenchmarkTestDTO(BaseModel):
    """
    BenchmarkTestDTO represents the data transfer object for benchmark test configuration.
    
    This DTO contains only the essential data fields for transferring benchmark test
    information between different layers of the application, without complex logic.

    Attributes:
        name (str): The name of the test configuration.
        dataset (DatasetDTO): The dataset used for benchmark.
        metric (dict): The metric used to evaluate the test.
        description (str): The prompt or scenario description for the test.
    """

    class Config:
        arbitrary_types_allowed = True

    # Name of the test
    name: str

    # Data used for benchmark
    dataset: Optional[DatasetDTO] = None

    # Metric used to evaluate the test
    metric: dict

    # Prompt or scenario description for the test
    description: str = ""

    def __str__(self) -> str:
        """String representation for debugging."""
        dataset_info = f"Dataset: {self.dataset.name}" if self.dataset else "Dataset: None"
        return (
            f"BenchmarkTestDTO(\n"
            f"  name: '{self.name}'\n"
            f"  {dataset_info}\n"
            f"  metric: {self.metric}\n"
            f"  description: '{self.description}'\n"
            f")"
        )
