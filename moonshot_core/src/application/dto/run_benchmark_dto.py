from pydantic import BaseModel


class RunBenchmarkRequestDTO(BaseModel):
    """
    RunBenchmarkRequestDTO represents the data transfer object for benchmark execution request.
    
    This DTO contains only the essential data fields for transferring benchmark execution
    request information between different layers of the application, without complex logic.

    Attributes:
        test_name (str): The name of the test to execute.
        dataset (str): The dataset identifier to use for the benchmark.
        metric (str): The metric identifier to use for evaluation.
        connector (str): The connector identifier to use for the benchmark.
    """

    class Config:
        arbitrary_types_allowed = True

    # The name of the test to execute
    test_name: str

    # The dataset identifier to use for the benchmark
    dataset: str

    # The metric identifier to use for evaluation
    metric: str

    # The connector identifier to use for the benchmark
    connector: str


class RunBenchmarkResponseDTO(BaseModel):
    """
    RunBenchmarkResponseDTO represents the data transfer object for benchmark execution response.
    
    This DTO contains only the essential data fields for transferring benchmark execution
    response information between different layers of the application, without complex logic.

    Attributes:
        test_name (str): The name of the test that was executed.
        message (str): A message describing the result of the benchmark execution.
    """

    class Config:
        arbitrary_types_allowed = True

    # The name of the test that was executed
    test_name: str

    # A message describing the result of the benchmark execution
    message: str
