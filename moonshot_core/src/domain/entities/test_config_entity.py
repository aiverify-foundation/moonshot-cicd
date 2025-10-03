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

    # Additional description for the test
    description: str = ""

    def __str__(self) -> str:
        """
        Returns a formatted string representation of the TestConfigEntity for debugging.
        
        Returns:
            str: A formatted string containing all entity attributes
        """
        lines = [
            f"TestConfigEntity:",
            f"  Name: {self.name}",
            f"  Type: {self.type.value if self.type else 'None'}",
            f"  Dataset: {self.dataset if self.dataset else 'None'}",
            f"  Prompt: {self.prompt if self.prompt else 'None'}",
        ]
        
        # Format attack_module
        if self.attack_module:
            lines.append("  Attack Module:")
            for key, value in self.attack_module.items():
                lines.append(f"    {key}: {value}")
        else:
            lines.append("  Attack Module: None")
        
        # Format metric
        if self.metric:
            lines.append("  Metric:")
            for key, value in self.metric.items():
                lines.append(f"    {key}: {value}")
        else:
            lines.append("  Metric: None")
        
        return "\n".join(lines)
