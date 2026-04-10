"""Session management utilities for SQLAlchemy."""

import os
import application.services.utils as utils

from functools import wraps
from pathlib import PosixPath
from contextlib import contextmanager
from domain.services.logger import configure_logger
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from alembic import command
from alembic.config import Config

# Process-local: when True, SessionManager._run_migrations skips Alembic (bundle workers).
_skip_alembic_upgrade: bool = False
logger = configure_logger(__name__)


def set_skip_alembic_upgrade(value: bool) -> None:
    """
    Set whether to skip Alembic upgrade for the next SessionManager init in this process.

    Used by multiprocessing worker entrypoints after the parent has migrated the same DB.
    """
    global _skip_alembic_upgrade
    _skip_alembic_upgrade = value


def singleton(cls):
    """Decorator that ensures a class has only one instance."""

    _instance = None
    _cls = cls

    @wraps(cls)
    def get_instance(*args, **kwargs):
        nonlocal _instance
        if _instance is None:
            _instance = _cls(*args, **kwargs)
        return _instance

    def reset_instance():
        nonlocal _instance
        _instance = None

    get_instance.get_instance = get_instance
    get_instance.reset_instance = reset_instance
    get_instance.get_database_url = lambda: get_instance().get_database_url()
    return get_instance


@singleton
class SessionManager:
    """
    Manages SQLAlchemy database sessions.
    
    This class provides a centralized way to create and manage database sessions
    for SQLAlchemy operations.
    
    Database URL is configured via the DATABASE_URL environment variable.
    If not set, defaults to the application SQLite database.
    """

    def get_database_url(self) -> str:
        """
        Get the database URL for SQLAlchemy and Alembic.

        Reads from MOONSHOT_DB_PATH environment variable if set,
        otherwise returns the default application SQLite database URL.

        Returns:
            str: The database URL to use for connections.
        """
        application_root_path: PosixPath = utils.get_application_root_path()
        default_sqlite_db_path: str = f"{application_root_path}/data/database/moonshot.db"
        sqlite_db_path: str = os.environ.get("MOONSHOT_DB_PATH", default_sqlite_db_path)
        sqlite_db_url: str = f"sqlite:///{sqlite_db_path}"
        return sqlite_db_url
    
    def __init__(self):
        """
        Initialize the session manager.

        Runs Alembic migrations (except for in-memory URLs) before creating the engine.
        Database URL is determined by get_database_url().
        """
        self.db_url = self.get_database_url()
        self._run_migrations()

        # Use StaticPool for SQLite to ensure thread-safety
        # check_same_thread=False for FastAPI's multi-threaded async operations
        # echo=True for SQL query logging
        self.engine: Engine = create_engine(
            self.db_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session.
        
        Yields:
            Session: SQLAlchemy session object.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    
    def _run_migrations(self) -> None:
        """Run Alembic migrations to initialize and update database schema. Skips for in-memory URLs."""
        if ":memory:" in self.db_url:
            return
        if _skip_alembic_upgrade:
            logger.debug("Skipping Alembic upgrade (worker process flag set)")
            return
        application_root_path = utils.get_application_root_path()
        alembic_ini_path: PosixPath = application_root_path / "alembic.ini"
        if not alembic_ini_path.exists():
            raise FileNotFoundError(f"Alembic config file not found at {alembic_ini_path}")
        
        # Run migrations to head (latest version)
        try:
            alembic_cfg = Config(str(alembic_ini_path))
            alembic_cfg.set_main_option("sqlalchemy.url", self.db_url)
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            print(f"Warning: Alembic migration failed: {e}")
            print("Database may already be initialized. Continuing...")
