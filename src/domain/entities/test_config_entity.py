from typing import Dict, Optional

from pydantic import BaseModel

from domain.services.enums.test_types import TestTypes


class TestConfigEntity(BaseModel):
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

    # Name of the test
    name: str

    # Type of test
    type: TestTypes

    # Module used for attack simulations, including parameters
    attack_module: Optional[Dict] = None

    # Data used for benchmark
    dataset: str = ""

    # Metric used to evaluate the test
    metric: dict

    # Prompt or scenario description for the test
    prompt: str = ""
