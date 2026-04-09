"""Tests for LlmProviderApiKeyService."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderApiKeyModel,
    LLMProviderModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.llm_provider_api_key_repository import LlmProviderApiKeyConflictError
from application.services.llm_provider_api_key_service import (
    LlmProviderApiKeyService,
    LlmProviderApiKeyUnknownProviderError,
)


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root: Path = Path(__file__).parent.parent.parent.parent
    db_path: Path = moonshot_core_root / "data" / "database" / "moonshot_pytest_api_key_svc.db"
    if db_path.exists():
        db_path.unlink()
    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def llm_provider_id(test_db_env) -> int:
    sm = SessionManager.get_instance()
    with sm.get_session() as session:
        p = LLMProviderModel(
            name="Svc ApiKey Provider",
            system_name="svc_api_key_provider",
            version=0,
        )
        session.add(p)
        session.flush()
        return int(p.id)


@pytest.fixture
def service(test_db_env):
    return LlmProviderApiKeyService()


class TestLlmProviderApiKeyService:
    def test_unknown_provider(self, service):
        with pytest.raises(LlmProviderApiKeyUnknownProviderError):
            service.create_api_key(999_999, "secret")

    def test_empty_api_key_rejected(self, service, llm_provider_id):
        with pytest.raises(ValueError, match="non-empty"):
            service.create_api_key(llm_provider_id, "")
        with pytest.raises(ValueError, match="non-empty"):
            service.update_api_key(llm_provider_id, "")

    def test_create_then_read_raw(self, service, llm_provider_id):
        service.create_api_key(llm_provider_id, "first-key")
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            row = (
                session.query(LLMProviderApiKeyModel)
                .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
                .one()
            )
            stored = row.encrypted_key
        assert stored == "first-key"

    def test_create_conflict(self, service, llm_provider_id):
        service.create_api_key(llm_provider_id, "a")
        with pytest.raises(LlmProviderApiKeyConflictError):
            service.create_api_key(llm_provider_id, "b")

    def test_update_changes_value(self, service, llm_provider_id):
        service.create_api_key(llm_provider_id, "old")
        service.update_api_key(llm_provider_id, "new")
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            row = (
                session.query(LLMProviderApiKeyModel)
                .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
                .one()
            )
            stored = row.encrypted_key
        assert stored == "new"
