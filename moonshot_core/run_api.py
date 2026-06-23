#!/usr/bin/env python3
"""
Script to run the FastAPI server for Moonshot CI/CD.
"""

import uvicorn

from domain.services.logger import configure_logger

configure_logger("moonshot.run_api")

from src.entrypoints.api import app

if __name__ == "__main__":
    uvicorn.run(
        "src.entrypoints.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        log_config=None,
    )
