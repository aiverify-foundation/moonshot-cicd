from typing import Optional

from pydantic import BaseModel, ConfigDict


class BenchmarkTestDatasetPromptEntity(BaseModel):
    """
    Domain entity for a single prompt in a benchmark test dataset.

    Mirrors the benchmark_test_dataset_prompt table.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    benchmark_test_dataset_id: Optional[int] = None
    prompt: str
    target: str
