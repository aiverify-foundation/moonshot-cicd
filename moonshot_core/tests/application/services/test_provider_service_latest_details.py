import pytest
from pathlib import Path

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderModel,
    LLMProviderModelModel,
    LLMProviderEndpointConfigModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.provider_service import ProviderService


@pytest.fixture(scope="function")
def test_db_path():
    """Create a temporary database path for testing ProviderService."""
    moonshot_core_root: Path = (
        Path(__file__).parent.parent.parent.parent  # .../moonshot_core
    )
    db_path: Path = moonshot_core_root / "data" / "database" / "moonshot_pytest.db"

    if db_path.exists():
        db_path.unlink()

    yield str(db_path)

    # DB cleanup is intentionally skipped as other tests may rely on it


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set up test database environment variable and reset SessionManager."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()

    yield

    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def provider_service(test_db_env):
    """Create a ProviderService instance backed by a real SessionManager/DB."""
    return ProviderService()


def _seed_provider_with_models_and_endpoints(system_name: str):
    """Insert provider rows plus associated models and endpoint configs."""
    session_manager = SessionManager.get_instance()
    with session_manager.get_session() as session:
        # two versions, ensure ordering by version desc picks the highest
        older = LLMProviderModel(
            name="Test Provider Old",
            system_name=system_name,
            version=0,
        )
        latest = LLMProviderModel(
            name="Test Provider Latest",
            system_name=system_name,
            version=1,
        )
        session.add(older)
        session.add(latest)
        session.flush()

        model_row = LLMProviderModelModel(
            llm_provider_id=latest.id,
            name="test-model",
        )
        endpoint_row = LLMProviderEndpointConfigModel(
            llm_provider_id=latest.id,
            name="test-endpoint",
        )
        session.add(model_row)
        session.add(endpoint_row)
        session.commit()

        return latest.id


class TestProviderServiceLatestDetails:
    def test_returns_none_when_no_provider(self, provider_service: ProviderService):
        """Service should return None when no provider exists for system_name."""
        details = provider_service.get_latest_provider_details_by_system_name(
            "nonexistent_system_name"
        )
        assert details is None

    def test_returns_latest_version_with_models_and_endpoints(
        self,
        provider_service: ProviderService,
    ):
        """Service should return latest-version provider plus related models and endpoints."""
        system_name = "test_system_name"
        latest_id = _seed_provider_with_models_and_endpoints(system_name)

        details = provider_service.get_latest_provider_details_by_system_name(
            system_name
        )

        assert details is not None
        assert details.provider.system_name == system_name
        assert details.provider.version == 1
        # ensure we picked the latest provider row
        assert str(latest_id) == details.provider.id

        assert len(details.models) == 1
        assert details.models[0].name == "test-model"

        assert len(details.endpoint_configs) == 1
        assert details.endpoint_configs[0].name == "test-endpoint"

