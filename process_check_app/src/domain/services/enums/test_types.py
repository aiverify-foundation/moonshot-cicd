from enum import Enum


class TestTypes(Enum):
    """
    Enum representing the types of tests.
    """

    # Represents a benchmark test
    BENCHMARK = "benchmark"

    # Represents a scan test
    SCAN = "scan"
