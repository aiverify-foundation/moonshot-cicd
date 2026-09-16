"""Tests for OpenRouter feature-flag gating in provider registration maps and listing."""

from unittest.mock import MagicMock

import pytest

from adapters.connector.openrouter_adapter import OpenRouterAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.database_connector_config_service import (
    get_system_name_to_adapter_module,
)
from application.services.provider_connector_env_key_service import (
    get_adapter_module_to_env,
)
from application.services.provider_service import (
    ProviderService,
    get_adapter_by_system_name,
)
from domain.entities.provider_entity import ProviderEntity
from domain.services import feature_flags
from domain.services.feature_flags import OPENROUTER_ADAPTER_SYSTEM_NAME


@pytest.fixture(scope="function")
def test_db_env(tmp_path, monkeypatch):
    db_path = tmp_path / "moonshot_openrouter_flag_pytest.db"
    monkeypatch.setenv("MOONSHOT_DB_PATH", str(db_path))
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


def test_maps_omit_openrouter_when_flag_off(monkeypatch):
    monkeypatch.setattr(feature_flags, "ENABLE_OPENROUTER", False)

    assert OPENROUTER_ADAPTER_SYSTEM_NAME not in get_system_name_to_adapter_module()
    assert OPENROUTER_ADAPTER_SYSTEM_NAME not in get_adapter_module_to_env()
    assert OPENROUTER_ADAPTER_SYSTEM_NAME not in get_adapter_by_system_name()


def test_maps_include_openrouter_when_flag_on(monkeypatch):
    monkeypatch.setattr(feature_flags, "ENABLE_OPENROUTER", True)

    assert (
        get_system_name_to_adapter_module()[OPENROUTER_ADAPTER_SYSTEM_NAME]
        == OPENROUTER_ADAPTER_SYSTEM_NAME
    )
    assert get_adapter_module_to_env()[OPENROUTER_ADAPTER_SYSTEM_NAME] == "OPENROUTER_API_KEY"
    assert get_adapter_by_system_name()[OPENROUTER_ADAPTER_SYSTEM_NAME] is OpenRouterAdapter


def test_list_providers_hides_openrouter_when_flag_off(test_db_env, monkeypatch):
    monkeypatch.setattr(feature_flags, "ENABLE_OPENROUTER", False)

    service = ProviderService()
    mock_repo = MagicMock()
    mock_repo.list_providers.return_value = [
        ProviderEntity(
            id="1",
            name="OpenAI",
            system_name="openai_adapter",
            version=1,
        ),
        ProviderEntity(
            id="2",
            name="OpenRouter",
            system_name=OPENROUTER_ADAPTER_SYSTEM_NAME,
            version=1,
        ),
    ]
    service.provider_repository = mock_repo

    dtos = service.list_providers()
    assert [d.system_name for d in dtos] == ["openai_adapter"]


def test_list_providers_includes_openrouter_when_flag_on(test_db_env, monkeypatch):
    monkeypatch.setattr(feature_flags, "ENABLE_OPENROUTER", True)

    service = ProviderService()
    mock_repo = MagicMock()
    mock_repo.list_providers.return_value = [
        ProviderEntity(
            id="1",
            name="OpenAI",
            system_name="openai_adapter",
            version=1,
        ),
        ProviderEntity(
            id="2",
            name="OpenRouter",
            system_name=OPENROUTER_ADAPTER_SYSTEM_NAME,
            version=1,
        ),
    ]
    service.provider_repository = mock_repo

    dtos = service.list_providers()
    assert [d.system_name for d in dtos] == [
        "openai_adapter",
        OPENROUTER_ADAPTER_SYSTEM_NAME,
    ]
