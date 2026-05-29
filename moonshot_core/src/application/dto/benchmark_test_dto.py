from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = ""
    # Name of the test
    name: str

    # Data used for benchmark
    dataset: Optional[DatasetDTO] = None

    # Metric used to evaluate the test
    metric: dict

    # Prompt or scenario description for the test
    description: str = ""

    # True when this test's metric uses an LLM as judge (e.g. Llama Guard annotator).
    requires_llm_aaj: bool = False

    # Metric-side connector system_name when requires_llm_aaj (e.g. together_adapter).
    metric_provider_system_name: Optional[str] = None

    # Evaluator model from moonshot_config metrics (connector_configurations.model).
    metric_grader_model_name: Optional[str] = None

    #: benchmark_test.id when loaded from the database (for start-benchmark-run subset selection).
    benchmark_test_id: Optional[int] = None

    #: Prompt-level rows from test_details.csv for this test's dataset (no row_id).
    details: Optional[list[dict[str, str]]] = None


