import logging
import os
from pathlib import Path

from rich.logging import RichHandler


def configure_logger(name: str):
    """
    Configures and returns a logger with a specified name.

    This function creates a logger and sets its level to INFO. It also creates a console handler,
    sets its level to INFO, and assigns a specific formatter to it. The formatter includes the
    timestamp, log level, filename, function name, line number, and the log message. Finally, the
    console handler is added to the logger.

    Args:
        name (str): The name of the logger to be created and configured.

    Returns:
        logging.Logger: The configured logger with the specified name.
    """
    log_extension = ".log"
    default_log_path = "data/results/ms.log"
    default_log_level = "INFO"

    # Read environment variables
    log_path = os.getenv("MS_LOG_PATH", default_log_path)
    log_level = os.getenv("MS_LOG_LEVEL", default_log_level).upper()

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s][%(filename)s::%(funcName)s(%(lineno)d)] %(message)s"
    )
    console_formatter = logging.Formatter("%(message)s")

    # Check name is valid
    if not name or not isinstance(name, str) or name is None:
        name = Path(__file__).stem

    # Check log level is valid
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_log_levels:
        log_level = "INFO"

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False

    # Check if there is already a stream handler
    if not any(
        isinstance(handler, logging.StreamHandler) for handler in logger.handlers
    ):
        # Create a Rich console handler
        console_handler = RichHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Create the directory if it does not exist
    file_path = Path(log_path).with_suffix(log_extension)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a file handler
    file_handler = logging.FileHandler(str(file_path))  # Convert Path object to string
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
