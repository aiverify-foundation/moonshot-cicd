"""Tests for domain.services.logger."""

import logging
import os
import sys
from io import StringIO
from pathlib import Path

import pytest

from domain.services import logger as logger_module
from domain.services.logger import configure_logger, get_logger


@pytest.fixture(autouse=True)
def reset_root_logging(monkeypatch, tmp_path):
    """Isolate logging configuration between tests."""
    monkeypatch.setenv("MS_LOG_PATH", str(tmp_path / "test.log"))
    logger_module._ROOT_LOGGING_CONFIGURED = False
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    for name in logger_module._UVICORN_LOGGER_NAMES:
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
    yield
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    logger_module._ROOT_LOGGING_CONFIGURED = False


def _moonshot_file_handlers() -> list[logging.FileHandler]:
    root = logging.getLogger()
    return [h for h in root.handlers if isinstance(h, logging.FileHandler)]


def _moonshot_console_handlers() -> list[logging.Handler]:
    root = logging.getLogger()
    return [
        h
        for h in root.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]


def test_configure_logger_attaches_single_file_handler():
    configure_logger("test.module.a")
    configure_logger("test.module.b")

    assert len(_moonshot_file_handlers()) == 1


def test_named_logger_uses_get_logger_without_extra_handlers():
    named = configure_logger("test.named")
    configure_logger("test.named")

    assert named is logging.getLogger("test.named")
    assert named.handlers == []


def test_get_logger_configures_root_without_prior_configure_logger():
    logger = get_logger("test.early.module")
    logger.info("early log message")

    assert len(_moonshot_file_handlers()) == 1
    log_text = Path(os.environ["MS_LOG_PATH"]).with_suffix(".log").read_text(encoding="utf-8")
    assert "early log message" in log_text


def test_repeated_get_logger_does_not_add_handlers():
    for _ in range(5):
        get_logger("adapters.driven.repository.sqlalchemy.benchmark_run_adapter")

    assert len(_moonshot_file_handlers()) == 1
    assert os.path.abspath(_moonshot_file_handlers()[0].baseFilename) == str(
        Path(os.environ["MS_LOG_PATH"]).with_suffix(".log").resolve()
    )


def test_uvicorn_loggers_propagate_and_write_to_file():
    configure_logger("entrypoints.api")

    access_logger = logging.getLogger("uvicorn.access")
    assert access_logger.propagate is True
    assert access_logger.handlers == []

    access_logger.info('127.0.0.1:8000 - "GET /api/health HTTP/1.1" 200')
    log_text = Path(os.environ["MS_LOG_PATH"]).with_suffix(".log").read_text(encoding="utf-8")
    assert "GET /api/health HTTP/1.1" in log_text


def test_rich_handler_uses_stdout():
    from rich.logging import RichHandler

    configure_logger("entrypoints.api")

    rich_handlers = [h for h in logging.getLogger().handlers if isinstance(h, RichHandler)]
    assert len(rich_handlers) == 1
    assert rich_handlers[0].console.file is sys.stdout
