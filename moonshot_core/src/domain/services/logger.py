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


def configure_file_logger(name: str, file_path: Path) -> logging.Logger:
    """
    Return a dedicated logger writing only to ``file_path``.

    Unlike :func:`configure_logger`, handlers are attached to the named
    logger itself (not root) and ``propagate`` is disabled, so records do
    not also reach the console or ``ms.log``. The message-only formatter
    keeps the file content exactly as emitted by the caller.

    Repeated calls are idempotent: exactly one ``FileHandler`` for the
    resolved path is kept. If the path changed since the last call (e.g.
    an env var was re-pointed), the stale handler is closed and replaced.

    The logger/handler levels are intentionally not gated by
    ``MS_LOG_LEVEL``: callers emit explicitly (e.g. one record per API
    failure), so a ``WARNING`` main-log setting must not drop them.
    """
    if not name or not isinstance(name, str):
        name = Path(__file__).stem

    resolved_path = Path(file_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path = resolved_path.resolve()
    target = os.path.abspath(str(resolved_path))

    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    kept_handler: logging.FileHandler | None = None
    for handler in logger.handlers[:]:
        if (
            kept_handler is None
            and isinstance(handler, logging.FileHandler)
            and os.path.abspath(handler.baseFilename) == target
        ):
            kept_handler = handler
            continue
        logger.removeHandler(handler)
        handler.close()

    if kept_handler is None:
        file_handler = logging.FileHandler(str(resolved_path), encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(file_handler)
    else:
        kept_handler.setLevel(logging.INFO)
        kept_handler.setFormatter(logging.Formatter("%(message)s"))

    return logger


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
