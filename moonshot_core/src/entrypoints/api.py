"""
FastAPI application for Moonshot CI/CD.
This module provides a REST API interface for the Moonshot benchmarking system.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path
from urllib.parse import urlparse
from domain.services.app_config import AppConfig
from domain.services.logger import configure_logger
from application.services.benchmark import BenchmarkService

# Configure the logger for this module
logger = configure_logger(__name__)

# Create FastAPI application instance
app = FastAPI(
    title="Moonshot CI/CD API",
    description="A REST API for the Moonshot benchmarking and red-teaming system",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


def get_build_directory() -> Path:
    """Get the build directory path from configuration."""
    app_config = AppConfig()
    build_dir_config = app_config.config.common.get("frontend_build_directory")

    # If the path is relative, make it relative to the API file's location
    if not os.path.isabs(build_dir_config):
        api_file_dir = Path(__file__).parent.parent.parent
        return api_file_dir / build_dir_config

    return Path(build_dir_config)


def is_valid_request(request: Request) -> bool:
    """
    Validate if the request is coming from the application and not direct access.
    This prevents users from accessing static files directly through the address bar.
    """
    # Check if request has a referer header (indicates it came from a page)
    referer = request.headers.get("referer")
    if not referer:
        logger.warning(
            f"Direct access attempt to {request.url} - no referer header"
        )
        return False

    # Parse the referer URL to get the host
    try:
        referer_parsed = urlparse(referer)
        request_parsed = urlparse(str(request.url))

        # Check if referer host matches request host (same origin)
        if referer_parsed.netloc != request_parsed.netloc:
            logger.warning(
                f"Cross-origin access attempt to {request.url} from {referer}"
            )
            return False

        # Check if referer is from the main application
        # (not a direct file access)
        if (not referer_parsed.path or referer_parsed.path == "/" or
                referer_parsed.path.startswith("/")):
            return True

    except Exception as e:
        logger.error(f"Error parsing referer header: {e}")
        return False

    return True


@app.get("/")
async def root():
    """Root endpoint that serves the main HTML file or returns a welcome message."""
    build_dir = get_build_directory()
    index_file = build_dir / "index.html"

    if index_file.exists():
        logger.info(f"Serving index.html from: {index_file}")
        return FileResponse(str(index_file))
    else:
        logger.warning(f"Index file not found at: {index_file}")
        return {"message": "Welcome to Moonshot CI/CD API"}


# Initialize the benchmark service
benchmark_service = BenchmarkService(None, None)


@app.get("/api/bundles")
async def view_all_bundles():
    """
    Get all available bundles.
    Returns a list of all bundles with their associated test configurations.
    """
    try:
        logger.info("Fetching all bundles")
        bundles = benchmark_service.get_all_bundles()
        logger.info(f"Successfully retrieved {len(bundles)} bundles")
        return {"bundles": bundles}
    except Exception as e:
        logger.error(f"Error fetching bundles: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.api_route("/{file_path:path}", methods=["GET", "HEAD"])
async def serve_static_files(file_path: str, request: Request):
    """Serve static files from the build directory with access control."""
    # Validate that the request is coming from the application, not direct access
    if not is_valid_request(request):
        logger.warning(f"Blocked direct access attempt to: {file_path}")
        raise HTTPException(
            status_code=403,
            detail="Direct access to static files is not allowed"
        )

    # Security check: detect path traversal attempts in the raw URL path
    raw_path = request.url.path
    if ".." in raw_path or "//" in raw_path:
        logger.warning(
            f"Path traversal attempt blocked in raw path: {raw_path}"
        )
        raise HTTPException(status_code=403, detail="Access denied")

    build_dir = get_build_directory()

    requested_file = build_dir / file_path

    # Additional security check: ensure the file is within the build directory
    try:
        requested_file.resolve().relative_to(build_dir.resolve())
    except ValueError:
        logger.warning(f"Path traversal attempt blocked: {file_path}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if the requested file exists
    if requested_file.exists() and requested_file.is_file():
        logger.info(f"Serving static file: {file_path}")
        return FileResponse(str(requested_file))
    
    # Check if it's a directory and has an index.html file (Next.js static export structure)
    elif requested_file.exists() and requested_file.is_dir():
        index_file = requested_file / "index.html"
        if index_file.exists():
            logger.info(f"Serving directory index file: {file_path}/index.html")
            return FileResponse(str(index_file))
    
    # If neither file nor directory with index.html exists, return 404
    logger.warning(f"Static file not found: {file_path}")
    raise HTTPException(status_code=404, detail="File not found")

# -------------------------------------------------------------------------------------------------
# This part assumes that the build directory is configured in moonshot_config.yaml
# and that the Next.js static files are located in the _next directory
# Those are the default locations for the static files generated by moonshot_portal_app
# when you call npm run build
# -------------------------------------------------------------------------------------------------
# Mount static files from configured build directory
build_dir = get_build_directory()
if build_dir.exists():
    # Note: Next.js static files are now served through the catch-all route handler
    # with access control to prevent direct URL access
    next_static_dir = build_dir / "_next"
    if next_static_dir.exists():
        logger.info(
            f"Next.js static files directory found at: {next_static_dir}"
        )
        logger.info(
            "Next.js static files will be served via the catch-all route "
            "handler with access control"
        )

    logger.info(f"Build directory found at: {build_dir}")
    logger.info(
        "Static files will be served via the catch-all route handler "
        "with access control"
    )
else:
    logger.warning(f"Build directory not found at: {build_dir}")

# Export the FastAPI app for external use
__all__ = ["app"]
