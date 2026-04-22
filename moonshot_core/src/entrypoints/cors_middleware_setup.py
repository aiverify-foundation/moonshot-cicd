"""
Register CORS middleware so browsers can preflight (OPTIONS) and call the API cross-origin.

Set MS_CORS_ORIGINS to a comma-separated list of allowed origins (e.g. http://localhost:3000).
If unset, a small localhost-oriented default list is used for local development.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

MS_CORS_ORIGINS_ENV = "MS_CORS_ORIGINS"

_DEFAULT_DEV_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _parse_cors_origins() -> list[str]:
    raw = os.environ.get(MS_CORS_ORIGINS_ENV, "").strip()
    if not raw:
        return list(_DEFAULT_DEV_ORIGINS)
    origins = [part.strip() for part in raw.split(",") if part.strip()]
    return origins if origins else list(_DEFAULT_DEV_ORIGINS)


def configure_cors_middleware(app: FastAPI) -> None:
    """Attach CORSMiddleware for API and successful OPTIONS preflight responses."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
