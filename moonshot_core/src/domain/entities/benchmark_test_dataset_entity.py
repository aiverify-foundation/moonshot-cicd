from typing import Optional

from pydantic import BaseModel, ConfigDict

from domain.entities.benchmark_test_dataset_prompt_entity import (
    BenchmarkTestDatasetPromptEntity,
)


class BenchmarkTestDatasetEntity(BaseModel):
    """
    Domain entity for a benchmark test dataset.

    Mirrors the benchmark_test_dataset table. Optionally holds
    prompts (benchmark_test_dataset_prompt rows) when loaded as an aggregate.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    version: int
    system_name: str
    description: Optional[str] = None
    license: Optional[str] = None
    reference: Optional[str] = None
    prompts: list[BenchmarkTestDatasetPromptEntity] = []
