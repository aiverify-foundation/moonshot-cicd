import logging
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

_ROOT_LOGGING_CONFIGURED = False

_UVICORN_LOGGER_NAMES = ("uvicorn", "uvicorn.error", "uvicorn.access")


def _resolve_log_file_path() -> Path:
    log_extension = ".log"
    default_log_path = "data/results/ms.log"
    log_path = os.getenv("MS_LOG_PATH", default_log_path)
    file_path = Path(log_path).with_suffix(log_extension)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path.resolve()


def _get_log_level() -> str:
    default_log_level = "INFO"
    log_level = os.getenv("MS_LOG_LEVEL", default_log_level).upper()
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_log_levels:
        log_level = "INFO"
    return log_level


def _has_rich_console_handler(handlers: list[logging.Handler]) -> bool:
    return any(isinstance(handler, RichHandler) for handler in handlers)


def _has_file_handler(handlers: list[logging.Handler], file_path: Path) -> bool:
    target = os.path.abspath(str(file_path))
    return any(
        isinstance(handler, logging.FileHandler)
        and os.path.abspath(handler.baseFilename) == target
        for handler in handlers
    )


def _configure_uvicorn_loggers(log_level: str) -> None:
    """Route uvicorn loggers through the root handlers (console + ms.log)."""
    for name in _UVICORN_LOGGER_NAMES:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(log_level)


def _ensure_root_logging() -> None:
    global _ROOT_LOGGING_CONFIGURED
    if _ROOT_LOGGING_CONFIGURED:
        return

    log_level = _get_log_level()
    file_path = _resolve_log_file_path()
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s][%(filename)s::%(funcName)s(%(lineno)d)] %(message)s"
    )
    console_formatter = logging.Formatter("%(message)s")

    root = logging.getLogger()
    root.setLevel(log_level)

    if not _has_rich_console_handler(root.handlers):
        console_handler = RichHandler(console=Console(file=sys.stdout))
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        root.addHandler(console_handler)

    if not _has_file_handler(root.handlers, file_path):
        file_handler = logging.FileHandler(str(file_path))
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        root.addHandler(file_handler)

    _configure_uvicorn_loggers(log_level)
    _ROOT_LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger after ensuring root handlers are configured.

    Use this instead of logging.getLogger() so logs reach console and ms.log
    even when configure_logger has not been called yet in this process.
    """
    if not name or not isinstance(name, str):
        name = Path(__file__).stem

    _ensure_root_logging()
    return logging.getLogger(name)


def configure_logger(name: str) -> logging.Logger:
    """
    Configures root logging once and returns a named logger.

    Handlers are attached only to the root logger so repeated calls do not
    open additional log files. Named loggers propagate to root by default.

    Args:
        name (str): The name of the logger to be returned.

    Returns:
        logging.Logger: The configured logger with the specified name.
    """
    if not name or not isinstance(name, str):
        name = Path(__file__).stem

    _ensure_root_logging()

    logger = logging.getLogger(name)
    logger.setLevel(_get_log_level())
    return logger
