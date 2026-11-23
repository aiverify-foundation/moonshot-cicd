"""Tests for domain.services.logger."""

import logging
import os
import sys
from io import StringIO
from pathlib import Path

import pytest

from domain.services import logger as logger_module
from domain.services.logger import configure_file_logger, configure_logger, get_logger


def _close_named_logger_handlers(name: str) -> None:
    named = logging.getLogger(name)
    for handler in named.handlers[:]:
        named.removeHandler(handler)
        handler.close()


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


def test_configure_file_logger_writes_only_to_its_file(tmp_path):
    name = "test.file_logger.only"
    target = tmp_path / "dedicated.log"
    try:
        file_logger = configure_file_logger(name, target)

        assert file_logger.propagate is False
        assert len(file_logger.handlers) == 1
        assert isinstance(file_logger.handlers[0], logging.FileHandler)
        # Does not configure root (no ms.log / console handlers attached).
        assert _moonshot_file_handlers() == []

        file_logger.error("dedicated message")
        assert target.read_text(encoding="utf-8") == "dedicated message\n"
    finally:
        _close_named_logger_handlers(name)


def test_configure_file_logger_is_idempotent(tmp_path):
    name = "test.file_logger.idempotent"
    target = tmp_path / "dedicated.log"
    try:
        for _ in range(3):
            file_logger = configure_file_logger(name, target)

        assert len(file_logger.handlers) == 1
        file_logger.error("only once")
        assert target.read_text(encoding="utf-8").count("only once") == 1
    finally:
        _close_named_logger_handlers(name)


def test_configure_file_logger_replaces_handler_on_path_change(tmp_path):
    name = "test.file_logger.path_change"
    first = tmp_path / "first.log"
    second = tmp_path / "second.log"
    try:
        file_logger = configure_file_logger(name, first)
        file_logger.error("first message")

        file_logger = configure_file_logger(name, second)
        assert len(file_logger.handlers) == 1
        assert Path(file_logger.handlers[0].baseFilename) == second.resolve()

        file_logger.error("second message")
        assert "second message" not in first.read_text(encoding="utf-8")
        assert "second message" in second.read_text(encoding="utf-8")
    finally:
        _close_named_logger_handlers(name)


def test_rich_handler_uses_stdout():
    from rich.logging import RichHandler

    configure_logger("entrypoints.api")

    rich_handlers = [h for h in logging.getLogger().handlers if isinstance(h, RichHandler)]
    assert len(rich_handlers) == 1
    assert rich_handlers[0].console.file is sys.stdout
