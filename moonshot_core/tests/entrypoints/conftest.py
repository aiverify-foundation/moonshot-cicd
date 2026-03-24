"""Isolated SQLite + shared.yaml seed for entrypoint tests that hit the real API DB."""

import os
import sys
from pathlib import Path

import pytest

MOONSHOT_CORE_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = MOONSHOT_CORE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from adapters.driven.repository.sqlalchemy.dataset_adapter import (  # noqa: E402
    SqlAlchemyDatasetRepository,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (  # noqa: E402
    MoonshotConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager  # noqa: E402
from application.services.benchmark_dataset_seed_service import (  # noqa: E402
    BenchmarkDatasetSeedService,
)
from application.services.file_dataset_repository import FileDatasetRepository  # noqa: E402
from application.services.file_shared_config_repository import (  # noqa: E402
    FileSharedConfigRepository,
)
from application.services.shared_config_seed_service import (  # noqa: E402
    SharedConfigSeedService,
)

SHARED_CONFIG_PATH = MOONSHOT_CORE_ROOT / "data" / "test_configs" / "shared.yaml"


@pytest.fixture(scope="session")
def test_db_path():
    """Dedicated DB for entrypoint tests; removed once at session start."""
    db_path = MOONSHOT_CORE_ROOT / "data" / "database" / "moonshot_pytest_entrypoints.db"
    if db_path.exists():
        db_path.unlink()
    return str(db_path)


@pytest.fixture(scope="session")
def test_db_env(test_db_path):
    """Set MOONSHOT_DB_PATH and reset SessionManager singleton."""
    old_val = os.environ.get("MOONSHOT_DB_PATH")
    os.environ["MOONSHOT_DB_PATH"] = test_db_path
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    if old_val is not None:
        os.environ["MOONSHOT_DB_PATH"] = old_val
    else:
        os.environ.pop("MOONSHOT_DB_PATH", None)


@pytest.fixture(scope="session")
def shared_config_seed_service(test_db_env):
    """Matches api lifespan / test_start_benchmark_run_integration construction."""
    return SharedConfigSeedService(
        moonshot_config_repository=MoonshotConfigAdapter(),
        shared_config_repository=FileSharedConfigRepository(),
        benchmark_dataset_seed_service=BenchmarkDatasetSeedService(
            source_dataset_repository=FileDatasetRepository(),
            target_dataset_repository=SqlAlchemyDatasetRepository(),
        ),
    )


@pytest.fixture(scope="session")
def seed_shared_config(shared_config_seed_service):
    """Load bundles/tests from shared.yaml (e.g. test-prompts) into the isolated DB."""
    assert SHARED_CONFIG_PATH.exists(), f"Shared config missing: {SHARED_CONFIG_PATH}"
    shared_config_seed_service.seed_if_test_file_changed(config_path=SHARED_CONFIG_PATH)
