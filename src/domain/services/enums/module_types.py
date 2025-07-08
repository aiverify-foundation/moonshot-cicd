from enum import Enum


class ModuleTypes(Enum):
    """
    Enum representing the various types of modules that can be loaded.
    """

    # Represents an attack module
    ATTACK_MODULE = "attack_module"

    # Represents a connector module
    CONNECTOR = "connector"

    # Represents a metric module
    METRIC = "metric"

    # Represents a prompt processor module
    PROMPT_PROCESSOR = "prompt_processor"
