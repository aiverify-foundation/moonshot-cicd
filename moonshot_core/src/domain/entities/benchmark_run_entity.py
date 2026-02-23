from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BenchmarkRunEntity(BaseModel):
    """
    Domain entity for a benchmark run (single run of an LLM provider endpoint).

    Mirrors the benchmark_run table.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    name: str
    status: str
    endpoint_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    llm_provider_id: Optional[int] = None
    llm_provider_model_id: Optional[int] = None
    llm_provider_endpoint_config_id: Optional[int] = None
