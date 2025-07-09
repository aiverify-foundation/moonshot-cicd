from enum import Enum


class FileTypes(Enum):
    """
    Enum representing the various types of files that can be loaded.
    """

    # Represents a dataset file
    DATASET = "dataset"

    # Represents a config file
    CONFIG = "config"

    # Represents a test file
    TEST_CONFIG = "test_config"
