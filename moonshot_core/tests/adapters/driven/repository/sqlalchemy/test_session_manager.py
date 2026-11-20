"""SessionManager SQLite connection settings."""

import pytest

from adapters.driven.repository.sqlalchemy.session_manager import SessionManager


@pytest.fixture
def session_manager(tmp_path, monkeypatch):
    """Point SessionManager at a temp DB and reset the singleton around the test."""
    db_path = tmp_path / "moonshot_busy_timeout.db"
    monkeypatch.setenv("MOONSHOT_DB_PATH", str(db_path))
    SessionManager.reset_instance()
    manager = SessionManager.get_instance()
    yield manager
    SessionManager.reset_instance()


def test_sqlite_busy_timeout_is_20_seconds(session_manager):
    """Writers wait 20 seconds for a file lock before raising database is locked."""
    with session_manager.engine.connect() as connection:
        busy_timeout_ms = connection.exec_driver_sql("PRAGMA busy_timeout").scalar()

    assert busy_timeout_ms == 20000
