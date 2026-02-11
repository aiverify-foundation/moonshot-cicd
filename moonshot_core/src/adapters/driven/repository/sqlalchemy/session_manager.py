"""Session management utilities for SQLAlchemy."""

import os
import application.services.utils as utils

from pathlib import PosixPath
from contextlib import contextmanager
from domain.services.logger import configure_logger
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from alembic import command
from alembic.config import Config


class SessionManager:
    """
    Manages SQLAlchemy database sessions.
    
    This class provides a centralized way to create and manage database sessions
    for SQLAlchemy operations.
    
    Database URL is configured via the DATABASE_URL environment variable.
    If not set, defaults to the application SQLite database.
    """
    logger = configure_logger(__name__)
    
    @classmethod
    def get_database_url(cls) -> str:
        """
        Get the database URL for SQLAlchemy and Alembic.
        
        Reads from DATABASE_URL environment variable if set,
        otherwise returns the default application SQLite database URL.
        
        Returns:
            str: The database URL to use for connections.
        """
        application_root_path: PosixPath = utils.get_application_root_path()
        print(f"[DEBUG:Kayden] application_root_path: {application_root_path}")
        default_sqlite_db_path: str = f"{application_root_path}/data/database/moonshot.db"
        sqlite_db_path: str = os.environ.get("MOONSHOT_DB_PATH", default_sqlite_db_path)
        sqlite_db_url: str = f"sqlite:///{sqlite_db_path}"
        return sqlite_db_url
    
    def __init__(self):
        """
        Initialize the session manager.
        
        Database URL is determined by get_database_url() class method.
        """
        self.db_url = self.get_database_url()
                
        # Use StaticPool for SQLite to ensure thread-safety
        # check_same_thread=False for FastAPI's multi-threaded async operations
        # echo=True for SQL query logging
        self.engine: Engine = create_engine(
            self.db_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=True,
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
    
    
    @classmethod
    def run_alembic_migrations(cls) -> None:
        """Run Alembic migrations to initialize and update database schema."""
        application_root_path = utils.get_application_root_path()
        
        # Get the path moonshot_core/alembic.ini
        alembic_ini_path: PosixPath = application_root_path / "alembic.ini"
        if not alembic_ini_path.exists():
            raise FileNotFoundError(f"Alembic config file not found at {alembic_ini_path}")
        
        # Run migrations to head (latest version)
        try:
            alembic_cfg = Config(str(alembic_ini_path))
            alembic_cfg.set_main_option("sqlalchemy.url", cls.get_database_url())

            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            print(f"Warning: Alembic migration failed: {e}")
            print("Database may already be initialized. Continuing...")
