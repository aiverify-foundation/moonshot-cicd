# Moonshot CI/CD FastAPI

This directory contains a FastAPI application for the Moonshot CI/CD system.

## Quick Start

### 1. Install Dependencies

```bash
cd moonshot_be
poetry install
```

### 2. Run the API Server

```bash
# Using the run script
python run_api.py

# Or using uvicorn directly
uvicorn src.entrypoints.api:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the API

- **API Base URL**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

## Available Endpoints

- `GET /` - Root endpoint (serves `../build/index.html` if available, otherwise welcome message)
- `GET /health` - Health check endpoint
- `GET /api/v1/status` - API status information
- `GET /static/*` - General static files from `../build` directory
- `GET /_next/*` - Next.js static assets from `../build` directory

## Testing

Run the API tests:

```bash
pytest tests/entrypoints/test_api.py -v
```

## Exporting the API

To export the FastAPI application for use in other contexts:

```bash
python export_api.py
```

This will generate:
- `openapi_schema.json` - OpenAPI specification
- `app_info.json` - Basic application information

## Usage in Other Applications

You can import and use the FastAPI app in other applications:

```python
from src.entrypoints.api import app

# Use the app directly
# or mount it in another FastAPI application
```

## Static Files

The API automatically serves static files from the `../build` directory:

- Next.js static assets are mounted at `/_next/*` path (for CSS, JS, and other Next.js assets)
- General static files are mounted at `/static/*` path
- If `../build/index.html` exists, it will be served at the root `/` endpoint
- The static files mount is only active if the `../build` directory exists

## Development

The API is structured to be easily extensible. To add new endpoints:

1. Add new route handlers in `src/entrypoints/api.py`
2. Add corresponding tests in `tests/entrypoints/test_api.py`
3. Update this README with new endpoint documentation
