#!/usr/bin/env python3
"""
Script to run the FastAPI server for Moonshot CI/CD.
"""

import uvicorn
from src.entrypoints.api import app
from src.adapters.driven.repository.sqlalchemy.session_manager import SessionManager

if __name__ == "__main__":

    # Create SQLite DB if not exists and run DB schema migrations to latest version
    SessionManager.run_alembic_migrations()

    uvicorn.run(
        "src.entrypoints.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
