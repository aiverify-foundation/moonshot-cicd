from enum import Enum


class TaskManagerStatus(Enum):
    """
    Enum representing the various statuses that a TaskManager can have.
    """

    # Task is pending and has not started yet
    PENDING = "pending"

    # Task is currently running
    RUNNING = "running"

    # Task encountered an error
    ERROR = "error"

    # Task completed successfully
    COMPLETED = "completed"

    # Task completed but with some errors
    COMPLETED_WITH_ERRORS = "completed_with_errors"
