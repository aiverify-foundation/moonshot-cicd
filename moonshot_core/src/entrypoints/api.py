"""
FastAPI application for Moonshot CI/CD.
This module provides a REST API interface for the Moonshot benchmarking system.
"""

from contextlib import asynccontextmanager
import sys

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import FileResponse, Response
import os
from pathlib import Path
from urllib.parse import urlparse
from domain.services.app_config import AppConfig
from domain.services.logger import configure_logger
from application.services.benchmark import BenchmarkService
from adapters.driven.repository.sqlalchemy.dataset_adapter import SqlAlchemyDatasetRepository
from adapters.driven.repository.sqlalchemy.sqlalchemy_benchmark_repository import (
    SqlAlchemyBenchmarkRepository,
)
from typing import List

# Provider/model-config service & DTOs
from application.services.provider_service import ProviderService
from application.dto.provider_dto import ProviderDTO
from application.dto.model_config_dto import (
    CreateDatabaseModelConfigBody,
    ModelConfigDTO,
    LLMProviderDetailsDTO,
    ProviderDatabaseConfigsDTO,
    UpdateDatabaseModelConfigBody,
)
from application.services.database_model_config_service import (
    DatabaseModelConfigBadRequestError,
    DatabaseModelConfigConflictError,
    DatabaseModelConfigNotFoundError,
    DatabaseModelConfigService,
)
from application.dto.run_bundle_dto import (
    BenchmarkRunResponseDTO,
    BenchmarkRunResultsResponseDTO,
    BenchmarkRunTestBundleResponseDTO,
    BenchmarkRunTestPromptResponseDTO,
    CheckBenchmarkRunNameResponseDTO,
    PatchBenchmarkRunTestPromptUserDTO,
    StartBenchmarkRunRequestDTO,
    StartBenchmarkRunResponseDTO,
)
from application.dto.seed_dto import SeedSharedConfigResponseDTO
from application.dto.llm_provider_api_key_dto import (
    SetLlmProviderApiKeyRequestDTO,
    SetLlmProviderApiKeyResponseDTO,
)
from application.services.provider_seed_service import ProviderSeedService
from application.services.custom_app_seed_service import CustomAppSeedService
from application.services.llm_provider_api_key_service import (
    LlmProviderApiKeyService,
    LlmProviderApiKeyUnknownProviderError,
)
# Benchmark execution service
from application.services.benchmark_execution_service import (
    BenchmarkExecutionService,
    BenchmarkRunTestSelectionError,
)
from application.services.database_connector_config_service import (
    DatabaseConnectorConfigError,
)
from application.services.database_custom_app_connector_config_service import (
    DatabaseCustomAppConnectorConfigError,
)
from application.dto.custom_app_config_dto import (
    CreateCustomAppBody,
    CreateCustomAppConfigBody,
    CustomAppConfigResponseDTO,
    CustomAppResponseDTO,
    SetCustomAppConfigSecretBody,
    TestCustomAppConnectionBody,
    TestCustomAppConnectionResponseDTO,
    UpdateCustomAppConfigBody,
)
from application.services.custom_app_connection_test_service import (
    CustomAppConnectionTestService,
)
from application.services.database_custom_app_config_service import (
    DatabaseCustomAppConfigBadRequestError,
    DatabaseCustomAppConfigConflictError,
    DatabaseCustomAppConfigNotFoundError,
    DatabaseCustomAppConfigService,
    DatabaseCustomAppService,
)
from application.services.custom_app_config_secret_service import (
    CustomAppConfigSecretService,
    CustomAppConfigSecretUnknownConfigError,
)
from application.services.benchmark_run_service import BenchmarkRunService
from application.services.benchmark_run_test_bundle_query_service import (
    BenchmarkRunTestBundleQueryService,
)
from application.services.benchmark_run_prompt_service import BenchmarkRunPromptService
from application.services.benchmark_run_results_query_service import (
    BenchmarkRunResultsQueryService,
)
from application.services.benchmark_run_results_export_service import (
    BenchmarkRunResultsExportError,
    BenchmarkRunResultsExportService,
)
from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import (
    SqlAlchemyBenchmarkRunTestStatusRepository,
)
# Comment out this import to disable CORS middleware ( This is used for local development only)
from entrypoints.cors_middleware_setup import configure_cors_middleware

# Configure the logger for this module
logger = configure_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks (e.g. seed shared config if changed) and yield for shutdown."""
    try:
        # Seed hardcoded LLM providers (idempotent, version-aware)
        ProviderSeedService().seed_hardcoded_providers()
        # Seed built-in custom apps shown in model selection
        CustomAppSeedService().seed_hardcoded_custom_apps()

        service = get_shared_config_seed_service()
        service.seed_if_test_file_changed()
    except Exception as e:
        logger.exception(f"Startup seed skipped or failed: {e}")
        sys.exit(1)

    yield
    # Shutdown (if needed later)


# Create FastAPI application instance
app = FastAPI(
    title="Moonshot CI/CD API",
    description="A REST API for the Moonshot benchmarking and red-teaming system",
    version="1.1.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

# Comment out this import to disable CORS middleware ( This is used for local development only)
configure_cors_middleware(app)


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


# Initialize the benchmark service (DB-backed bundles/tests; datasets from benchmark_test_dataset)
_sqlalchemy_dataset_repository = SqlAlchemyDatasetRepository()
benchmark_service = BenchmarkService(
    SqlAlchemyBenchmarkRepository(_sqlalchemy_dataset_repository),
    _sqlalchemy_dataset_repository,
)
provider_service = ProviderService()
database_model_config_service = DatabaseModelConfigService()
benchmark_execution_service = BenchmarkExecutionService()
llm_provider_api_key_service = LlmProviderApiKeyService()
database_custom_app_service = DatabaseCustomAppService()
database_custom_app_config_service = DatabaseCustomAppConfigService()
custom_app_config_secret_service = CustomAppConfigSecretService()
custom_app_connection_test_service = CustomAppConnectionTestService(
    secret_service=custom_app_config_secret_service,
)

# Lazy-initialized SharedConfigSeedService for seed-if-testfile-changed
_shared_config_seed_service = None


def get_shared_config_seed_service():
    """Get or create SharedConfigSeedService with full deps for seed_if_test_file_changed."""
    global _shared_config_seed_service
    if _shared_config_seed_service is None:
        from application.services.shared_config_seed_service import SharedConfigSeedService
        from application.services.file_shared_config_repository import FileSharedConfigRepository
        from application.services.benchmark_dataset_seed_service import BenchmarkDatasetSeedService
        from application.services.file_dataset_repository import FileDatasetRepository
        from adapters.driven.repository.sqlalchemy.dataset_adapter import (
            SqlAlchemyDatasetRepository,
        )
        from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (
            MoonshotConfigAdapter,
        )
        moonshot_config = MoonshotConfigAdapter()
        shared_config_repo = FileSharedConfigRepository()
        dataset_seed = BenchmarkDatasetSeedService(
            source_dataset_repository=FileDatasetRepository(),
            target_dataset_repository=SqlAlchemyDatasetRepository(),
        )
        _shared_config_seed_service = SharedConfigSeedService(
            moonshot_config_repository=moonshot_config,
            shared_config_repository=shared_config_repo,
            benchmark_dataset_seed_service=dataset_seed,
        )
    return _shared_config_seed_service



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


@app.get("/api/providers", response_model=List[ProviderDTO])
async def list_providers():
    """Get all LLM providers as DTOs."""
    try:
        providers = provider_service.list_providers()
        return providers
    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list providers")


@app.get(
    "/api/providers/with-database-model-configs",
    response_model=List[ProviderDatabaseConfigsDTO],
)
async def list_providers_with_database_model_configs():
    """
    Each llm_provider row with model configs from llm_provider_model_config and parameter rows only
    (no file or legacy SQLite model-config store).
    """
    try:
        return provider_service.list_providers_with_database_model_configs()
    except Exception as e:
        logger.error(f"Error listing providers with database model configs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list providers with database model configs",
        )


@app.post(
    "/api/database-model-configs",
    response_model=ModelConfigDTO,
)
async def create_database_model_config(
    payload: CreateDatabaseModelConfigBody, response: Response
):
    """Create a new database-backed model config and its own llm_provider_model row."""
    try:
        dto, _created = database_model_config_service.create(payload)
        response.status_code = 201
        return dto
    except DatabaseModelConfigBadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseModelConfigConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating database model config: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create database model config",
        )


@app.put("/api/database-model-configs/{config_id}", response_model=ModelConfigDTO)
async def update_database_model_config(
    config_id: int,
    payload: UpdateDatabaseModelConfigBody,
):
    """Update a database-backed llm_provider_model_config row and replace its parameters."""
    try:
        return database_model_config_service.update(config_id, payload)
    except DatabaseModelConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseModelConfigBadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseModelConfigConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating database model config {config_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update database model config",
        )


@app.get(
    "/api/providers/by-system-name/{system_name}/latest-details",
    response_model=LLMProviderDetailsDTO,
)
async def get_latest_provider_details_by_system_name(
    system_name: str,
):
    """
    Get the latest-version provider and its related models and endpoint configs for a system_name.
    """
    try:
        details = provider_service.get_latest_provider_details_by_system_name(system_name)
        if details is None:
            raise HTTPException(
                status_code=404,
                detail=f"No provider found for system_name={system_name!r}",
            )
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching latest provider details for system_name={system_name}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch latest provider details",
        )


@app.get("/api/providers/{provider_id}/model-configs", response_model=List[ModelConfigDTO])
async def get_model_configs_by_provider(provider_id: int):
    """Get all model configs for a provider ID, returned as DTOs."""
    try:
        configs = provider_service.get_model_configs_by_provider_id(provider_id)
        return configs
    except Exception as e:
        logger.error(f"Error fetching model configs for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model configs")


@app.post(
    "/api/providers/{provider_id}/api-key",
    response_model=SetLlmProviderApiKeyResponseDTO,
    status_code=201,
)
async def set_llm_provider_api_key(
    provider_id: int,
    payload: SetLlmProviderApiKeyRequestDTO,
):
    """
    Register or replace an encrypted API key for an llm_provider row (write-only).

    The plaintext key is never returned. There is no authentication on this API yet; use only
    on trusted networks (e.g. local dev) until auth is added.
    """
    try:
        llm_provider_api_key_service.set_api_key(provider_id, payload.api_key)
        return SetLlmProviderApiKeyResponseDTO(message="API key stored")
    except LlmProviderApiKeyUnknownProviderError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error storing API key for provider {provider_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store provider API key",
        )


@app.post("/api/model-configs", response_model=ModelConfigDTO)
async def create_model_config(payload: ModelConfigDTO):
    """Create a new model configuration using DTO."""
    try:
        created = provider_service.create_model_config(payload)
        return created
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating model config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create model config")


@app.put("/api/model-configs", response_model=ModelConfigDTO)
async def update_model_config(payload: ModelConfigDTO):
    """Update an existing model configuration (matched by name) using DTO."""
    try:
        updated = provider_service.update_model_config(payload)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating model config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update model config")


@app.delete("/api/model-configs/{config_id}")
async def delete_model_config(config_id: str):
    """Delete a model configuration by ID or name."""
    try:
        deleted = provider_service.delete_model_config(config_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Model config not found")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete model config")


@app.post("/api/start-benchmark-run", response_model=StartBenchmarkRunResponseDTO)
async def start_benchmark_run(request: StartBenchmarkRunRequestDTO) -> StartBenchmarkRunResponseDTO:
    """
    Start a benchmark run (multiple bundles in separate daemon processes).

    Delegates to BenchmarkExecutionService.start_benchmark_run.

    Returns:
        Response with a message that the benchmark run has started successfully.
    """
    try:
        benchmark_execution_service.start_benchmark_run(
            run_name=request.run_name,
            bundle_names=request.bundle_names,
            llm_provider_id=request.llm_provider_id,
            llm_provider_model_id=request.llm_provider_model_id,
            llm_provider_model_config_id=request.llm_provider_model_config_id,
            custom_app_id=request.custom_app_id,
            custom_app_config_id=request.custom_app_config_id,
            tests_by_bundle=request.tests_by_bundle,
        )
        return StartBenchmarkRunResponseDTO(message="Benchmark run started successfully.")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BenchmarkRunTestSelectionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DatabaseConnectorConfigError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DatabaseCustomAppConnectorConfigError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error starting benchmark run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start benchmark run: {str(e)}")


@app.get("/api/custom-apps", response_model=List[CustomAppResponseDTO])
async def list_custom_apps() -> List[CustomAppResponseDTO]:
    """List all custom apps."""
    try:
        return database_custom_app_service.list_apps()
    except Exception as e:
        logger.error(f"Error listing custom apps: {e}")
        raise HTTPException(status_code=500, detail="Failed to list custom apps")


@app.post("/api/custom-apps", response_model=CustomAppResponseDTO)
async def create_custom_app(payload: CreateCustomAppBody, response: Response):
    """Create a new custom app."""
    try:
        dto = database_custom_app_service.create_app(payload)
        response.status_code = 201
        return dto
    except Exception as e:
        logger.error(f"Error creating custom app: {e}")
        raise HTTPException(status_code=500, detail="Failed to create custom app")


@app.get(
    "/api/custom-apps/{app_id}/configs",
    response_model=List[CustomAppConfigResponseDTO],
)
async def list_custom_app_configs(app_id: int) -> List[CustomAppConfigResponseDTO]:
    """List configs for a custom app."""
    try:
        return database_custom_app_config_service.list_configs(app_id)
    except DatabaseCustomAppConfigBadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing custom app configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list custom app configs")


@app.post(
    "/api/custom-apps/{app_id}/configs",
    response_model=CustomAppConfigResponseDTO,
)
async def create_custom_app_config(
    app_id: int, payload: CreateCustomAppConfigBody, response: Response
):
    """Create a custom app config with parameters."""
    try:
        dto = database_custom_app_config_service.create(app_id, payload)
        response.status_code = 201
        return dto
    except DatabaseCustomAppConfigBadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseCustomAppConfigConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating custom app config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create custom app config")


@app.put(
    "/api/custom-apps/configs/{config_id}",
    response_model=CustomAppConfigResponseDTO,
)
async def update_custom_app_config(
    config_id: int, payload: UpdateCustomAppConfigBody
) -> CustomAppConfigResponseDTO:
    """Update a custom app config and replace its parameters."""
    try:
        return database_custom_app_config_service.update(config_id, payload)
    except DatabaseCustomAppConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseCustomAppConfigConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DatabaseCustomAppConfigBadRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating custom app config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update custom app config")


@app.post(
    "/api/custom-apps/test-connection",
    response_model=TestCustomAppConnectionResponseDTO,
)
async def test_custom_app_connection(
    payload: TestCustomAppConnectionBody,
) -> TestCustomAppConnectionResponseDTO:
    """Probe a custom app configuration with a live HTTP request."""
    try:
        return await custom_app_connection_test_service.test_connection(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error testing custom app connection: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to test custom app connection"
        )


@app.put("/api/custom-apps/configs/{config_id}/secrets/{key}")
async def set_custom_app_config_secret(
    config_id: int, key: str, payload: SetCustomAppConfigSecretBody
) -> dict:
    """Set or replace an encrypted secret for a custom app config."""
    try:
        custom_app_config_secret_service.set_secret(config_id, key, payload.secret)
        return {"message": "Secret stored successfully."}
    except CustomAppConfigSecretUnknownConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting custom app config secret: {e}")
        raise HTTPException(status_code=500, detail="Failed to set custom app config secret")


@app.get(
    "/api/benchmark-runs",
    response_model=List[BenchmarkRunResponseDTO],
)
async def list_benchmark_runs() -> List[BenchmarkRunResponseDTO]:
    """
    Return all benchmark runs (id, name, status, times, LLM FKs).

    Uses BenchmarkRunService.get_all_runs.
    """
    try:
        service = BenchmarkRunService()
        entities = service.get_all_runs()
        return [
            BenchmarkRunResponseDTO.model_validate(e.model_dump())
            for e in entities
        ]
    except Exception as e:
        logger.error(f"Error listing benchmark runs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list benchmark runs: {str(e)}",
        )


@app.get(
    "/api/benchmark-runs/check-name",
    response_model=CheckBenchmarkRunNameResponseDTO,
)
async def check_benchmark_run_name(run_name: str) -> CheckBenchmarkRunNameResponseDTO:
    """
    Check whether a benchmark run name is available (not already in use).

    Uses BenchmarkRunService.get_run_by_name on the trimmed name.
    """
    trimmed = run_name.strip()
    if not trimmed:
        raise HTTPException(status_code=400, detail="run_name must not be empty.")
    try:
        service = BenchmarkRunService()
        existing = service.get_run_by_name(trimmed)
        return CheckBenchmarkRunNameResponseDTO(
            run_name=trimmed,
            available=existing is None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking benchmark run name: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check benchmark run name: {str(e)}",
        )


@app.get(
    "/api/benchmark-runs/{run_id}",
    response_model=BenchmarkRunResponseDTO,
)
async def get_benchmark_run(run_id: int) -> BenchmarkRunResponseDTO:
    """
    Return a single benchmark run by id.

    Uses BenchmarkRunService.get_run_by_id. 404 if not found.
    """
    try:
        service = BenchmarkRunService()
        entity = service.get_run_by_id(run_id)
        if entity is None:
            raise HTTPException(
                status_code=404,
                detail=f"Benchmark run not found: run_id={run_id}",
            )
        return BenchmarkRunResponseDTO.model_validate(entity.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching benchmark run run_id={run_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch benchmark run: {str(e)}",
        )


@app.get(
    "/api/benchmark-runs/{run_id}/prompts",
    response_model=List[BenchmarkRunTestPromptResponseDTO],
)
async def get_benchmark_run_prompts(run_id: int) -> List[BenchmarkRunTestPromptResponseDTO]:
    """
    Return all benchmark run test prompts for the given benchmark run id.

    Uses BenchmarkRunResultsQueryService.list_prompt_dtos. Returns an empty list
    if the run has no run-test statuses or prompts.
    """
    try:
        return BenchmarkRunResultsQueryService().list_prompt_dtos(run_id)
    except Exception as e:
        logger.error(f"Error fetching run prompts for run_id={run_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch run prompts: {str(e)}",
        )


@app.get(
    "/api/benchmark-runs/{run_id}/results",
    response_model=BenchmarkRunResultsResponseDTO,
)
async def get_benchmark_run_results(run_id: int) -> BenchmarkRunResultsResponseDTO:
    """
    Return run header, bundle summaries (from benchmark_run_test_bundle), and all prompts
    with test_id and test_name for the results UI. ``test_margin_of_error`` lists
    ``{test_id, margin_of_error}`` per ``benchmark_test`` (95% t-interval on the mean of
    per-prompt ``score`` for that test; ``0`` when there are two or fewer scored prompts);
    alpha is fixed in the service layer.
    """
    try:
        service = BenchmarkRunResultsQueryService()
        dto = service.get_results(run_id)
        if dto is None:
            raise HTTPException(
                status_code=404,
                detail=f"Benchmark run not found: run_id={run_id}",
            )
        return dto
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching run results for run_id={run_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch run results: {str(e)}",
        )


@app.get("/api/benchmark-runs/{run_id}/export")
async def export_benchmark_run_results(run_id: int) -> Response:
    """
    Download GA Schema1 JSON for a completed benchmark run.

    ``run_metadata.test_id`` equals ``run_metadata.run_id`` (the run name). One
    ``run_results[]`` entry is emitted per benchmark test in the run.
    """
    try:
        run_service = BenchmarkRunService()
        run_entity = run_service.get_run_by_id(run_id)
        if run_entity is None:
            raise HTTPException(
                status_code=404,
                detail=f"Benchmark run not found: run_id={run_id}",
            )

        export_service = BenchmarkRunResultsExportService()
        payload_json = export_service.export_run_json(run_id, redact_secrets=True)
        if payload_json is None:
            raise HTTPException(
                status_code=404,
                detail=f"Benchmark run not found: run_id={run_id}",
            )

        filename = f"{run_entity.name}.json"
        return Response(
            content=payload_json,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except BenchmarkRunResultsExportError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting run results for run_id={run_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export run results: {str(e)}",
        )


@app.patch(
    "/api/benchmark-run-test-prompts/{prompt_id}",
    response_model=BenchmarkRunTestPromptResponseDTO,
)
async def patch_benchmark_run_test_prompt_user_feedback(
    prompt_id: int, body: PatchBenchmarkRunTestPromptUserDTO
) -> BenchmarkRunTestPromptResponseDTO:
    """
    Update user verdict (user_evaluation) and notes (user_notes) for one prompt row.
    Identified by benchmark_run_test_prompt.id (globally unique).
    """
    try:
        prompt_service = BenchmarkRunPromptService()
        updated = prompt_service.patch_user_feedback(
            prompt_id,
            body.user_evaluation,
            body.user_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=f"Benchmark run test prompt not found: prompt_id={prompt_id}",
        )
    status_repo = SqlAlchemyBenchmarkRunTestStatusRepository()
    status_entity = status_repo.get_by_id(updated.run_test_id)
    if status_entity is None:
        raise HTTPException(
            status_code=500,
            detail="Run test status missing for updated prompt row",
        )
    run_id = status_entity.run_id
    return BenchmarkRunResultsQueryService().prompt_dto_for_entity(run_id, updated)


@app.get(
    "/api/benchmark-runs/{run_id}/run-test-bundles",
    response_model=List[BenchmarkRunTestBundleResponseDTO],
)
async def get_benchmark_run_test_bundles(
    run_id: int,
) -> List[BenchmarkRunTestBundleResponseDTO]:
    """
    Return all benchmark_run_test_bundle rows for the given benchmark run id.

    Uses BenchmarkRunTestBundleQueryService.get_all_by_run_id. Returns an empty list
    if the run has no rows.
    """
    try:
        service = BenchmarkRunTestBundleQueryService()
        entities = service.get_all_by_run_id(run_id)
        return [
            BenchmarkRunTestBundleResponseDTO.model_validate(e.model_dump())
            for e in entities
        ]
    except Exception as e:
        logger.error(f"Error fetching run-test-bundles for run_id={run_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch run-test-bundles: {str(e)}",
        )


@app.post("/api/seed-shared-config-if-changed", response_model=SeedSharedConfigResponseDTO)
async def seed_shared_config_if_changed() -> SeedSharedConfigResponseDTO:
    """
    Seed benchmark datasets and bundles/tests/groupings from the shared config file
    only if the test file has changed since the last seed (mtime check).

    Uses the default config path from AppConfig (e.g. data/test_configs/shared.yaml).
    Returns whether seeding was performed and a short message.
    """
    try:
        service = get_shared_config_seed_service()
        did_seed = service.seed_if_test_file_changed()
        if did_seed:
            return SeedSharedConfigResponseDTO(
                seeded=True,
                message="Seeding ran: datasets and bundles/tests/groupings updated.",
            )
        return SeedSharedConfigResponseDTO(
            seeded=False,
            message="Skipped: shared config not changed since last seed.",
        )
    except FileNotFoundError as e:
        logger.warning(f"Seed config file not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning(f"Seed validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during seed-if-changed: {e}")
        raise HTTPException(status_code=500, detail="Failed to run seed-if-changed.")


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
