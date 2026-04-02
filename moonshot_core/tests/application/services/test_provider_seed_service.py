from typing import List

import pytest
from pathlib import Path

from adapters.connector.openai_adapter import OpenAIAdapter
from adapters.connector.together_adapter import TogetherAdapter
from adapters.driven.repository.sqlalchemy.llm_provider_adapter import LLMProviderAdapter
from adapters.driven.repository.sqlalchemy.llm_provider_models import LLMProviderModel
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.provider_seed_service import ProviderSeedService
from domain.entities.provider_entity import ProviderEntity


@pytest.fixture(scope="function")
def test_db_path():
    """Create a temporary database path for testing."""
    moonshot_core_root: Path = Path(__file__).parent.parent.parent.parent
    db_path: Path = moonshot_core_root / "data" / "database" / "moonshot_provider_seed_pytest.db"

    if db_path.exists():
        db_path.unlink()

    yield str(db_path)

    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set up test database environment variable and reset SessionManager."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def provider_seed_service(test_db_env):
    adapter = LLMProviderAdapter()
    return ProviderSeedService(provider_repository=adapter)


def _get_providers_for_system_name(system_name: str) -> List[ProviderEntity]:
    adapter = LLMProviderAdapter()
    providers = adapter.list_providers()
    return [p for p in providers if p.system_name == system_name]


def _insert_provider_raw(system_name: str, version: int) -> None:
    with SessionManager.get_instance().get_session() as session:
        model = LLMProviderModel(name=system_name, system_name=system_name, version=version)
        session.add(model)
        session.flush()


def test_scenario_1_provider_does_not_exist(provider_seed_service):
    """
    Scenario 1: Provider does not exist in the database.
    When the service runs and no matching system_name is found,
    a new row is inserted for that provider.
    """
    provider_seed_service.seed_hardcoded_providers()

    # OpenAI
    providers = _get_providers_for_system_name(OpenAIAdapter.SYSTEM_NAME)
    assert len(providers) == 1
    assert providers[0].version == OpenAIAdapter.VERSION

    # TogetherAI
    providers = _get_providers_for_system_name(TogetherAdapter.SYSTEM_NAME)
    assert len(providers) == 1
    assert providers[0].version == TogetherAdapter.VERSION


def test_scenario_2_provider_exists_with_lower_version(provider_seed_service):
    """
    Scenario 2: Provider exists but hardcoded version is higher.
    Use existing version=0 and hardcoded version=1.
    """
    system_name = OpenAIAdapter.SYSTEM_NAME
    hardcoded_version = OpenAIAdapter.VERSION

    _insert_provider_raw(system_name=system_name, version=hardcoded_version - 1)

    provider_seed_service.seed_hardcoded_providers()

    providers = _get_providers_for_system_name(system_name)
    versions = sorted(p.version for p in providers)
    assert versions == [0, hardcoded_version]


def test_scenario_3_provider_exists_with_same_version(provider_seed_service):
    """
    Scenario 3: Provider exists with the same version.
    When service runs, no new row is inserted.
    """
    system_name = OpenAIAdapter.SYSTEM_NAME
    hardcoded_version = OpenAIAdapter.VERSION

    _insert_provider_raw(system_name=system_name, version=hardcoded_version)

    provider_seed_service.seed_hardcoded_providers()

    providers = _get_providers_for_system_name(system_name)
    assert len(providers) == 1
    assert providers[0].version == hardcoded_version


def test_scenario_4_provider_exists_with_higher_version(provider_seed_service):
    """
    Scenario 4: Provider exists with a higher version than hardcoded.
    When service runs, no new row is inserted.
    """
    system_name = OpenAIAdapter.SYSTEM_NAME
    hardcoded_version = OpenAIAdapter.VERSION

    _insert_provider_raw(system_name=system_name, version=hardcoded_version + 1)

    provider_seed_service.seed_hardcoded_providers()

    providers = _get_providers_for_system_name(system_name)
    assert len(providers) == 1
    assert providers[0].version == hardcoded_version + 1


def test_scenario_5_service_run_multiple_times(provider_seed_service):
    """
    Scenario 5: Service is run multiple times with no changes to hardcoded data.
    No duplicate rows are created and no errors are thrown.
    """
    provider_seed_service.seed_hardcoded_providers()
    provider_seed_service.seed_hardcoded_providers()

    # OpenAI
    providers = _get_providers_for_system_name(OpenAIAdapter.SYSTEM_NAME)
    assert len(providers) == 1
    assert providers[0].version == OpenAIAdapter.VERSION

    # TogetherAI
    providers = _get_providers_for_system_name(TogetherAdapter.SYSTEM_NAME)
    assert len(providers) == 1
    assert providers[0].version == TogetherAdapter.VERSION

