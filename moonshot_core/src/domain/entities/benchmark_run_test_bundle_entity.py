from typing import Optional

from pydantic import BaseModel, ConfigDict


class BenchmarkRunTestBundleEntity(BaseModel):
    """
    Domain entity linking a benchmark run to (test_bundle_id, test_id).

    Mirrors the benchmark_run_test_bundle table.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[int] = None
    run_id: int
    test_bundle_id: int
    test_id: int
