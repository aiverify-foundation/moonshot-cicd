"""Tests for LLMProviderApiKeyAdapter."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.llm_provider_api_key_adapter import (
    LLMProviderApiKeyAdapter,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderApiKeyModel,
    LLMProviderModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.ports.llm_provider_api_key_repository import (
    LlmProviderApiKeyAmbiguousError,
    LlmProviderApiKeyConflictError,
    LlmProviderApiKeyNotFoundError,
)
from domain.services.secret_encryption import EncryptedApiKeyFields


def _fake_encrypted_fields(*, tag: bytes = b"t" * 16) -> EncryptedApiKeyFields:
    return EncryptedApiKeyFields(
        encrypted_key=base64.b64encode(b"ciphertext").decode("ascii"),
        salt=base64.b64encode(b"s" * 32).decode("ascii"),
        nonce=base64.b64encode(b"n" * 12).decode("ascii"),
        authentication_tag=base64.b64encode(tag).decode("ascii"),
    )


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root: Path = Path(__file__).parent.parent.parent.parent.parent.parent
    db_path: Path = moonshot_core_root / "data" / "database" / "moonshot_pytest_api_key.db"
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
def api_key_adapter(test_db_env):
    return LLMProviderApiKeyAdapter()


@pytest.fixture
def llm_provider_id(test_db_env) -> int:
    sm = SessionManager.get_instance()
    with sm.get_session() as session:
        p = LLMProviderModel(
            name="ApiKey Test Provider",
            system_name="api_key_test_provider",
            version=0,
        )
        session.add(p)
        session.flush()
        return int(p.id)


class TestLLMProviderApiKeyAdapter:
    def test_insert_then_conflict(self, api_key_adapter, llm_provider_id):
        api_key_adapter.insert(llm_provider_id, _fake_encrypted_fields())
        with pytest.raises(LlmProviderApiKeyConflictError):
            api_key_adapter.insert(llm_provider_id, _fake_encrypted_fields())

    def test_update_not_found(self, api_key_adapter, llm_provider_id):
        with pytest.raises(LlmProviderApiKeyNotFoundError):
            api_key_adapter.update(llm_provider_id, _fake_encrypted_fields())

    def test_insert_then_update(self, api_key_adapter, llm_provider_id):
        first = _fake_encrypted_fields()
        second = EncryptedApiKeyFields(
            encrypted_key=base64.b64encode(b"second-ct").decode("ascii"),
            salt=base64.b64encode(b"a" * 32).decode("ascii"),
            nonce=base64.b64encode(b"b" * 12).decode("ascii"),
            authentication_tag=base64.b64encode(b"c" * 16).decode("ascii"),
        )
        api_key_adapter.insert(llm_provider_id, first)
        api_key_adapter.update(llm_provider_id, second)

        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            row = (
                session.query(LLMProviderApiKeyModel)
                .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
                .one()
            )
            stored = row.encrypted_key
            assert stored == second.encrypted_key
            assert row.salt == second.salt

    def test_update_ambiguous(self, api_key_adapter, llm_provider_id):
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            session.add(
                LLMProviderApiKeyModel(
                    llm_provider_id=llm_provider_id,
                    encrypted_key="a",
                    salt="b",
                    nonce="c",
                    authentication_tag="d",
                )
            )
            session.add(
                LLMProviderApiKeyModel(
                    llm_provider_id=llm_provider_id,
                    encrypted_key="a2",
                    salt="b2",
                    nonce="c2",
                    authentication_tag="d2",
                )
            )

        with pytest.raises(LlmProviderApiKeyAmbiguousError):
            api_key_adapter.update(llm_provider_id, _fake_encrypted_fields())

    def test_replace_clears_prior_rows(self, api_key_adapter, llm_provider_id):
        api_key_adapter.insert(llm_provider_id, _fake_encrypted_fields())
        replacement = EncryptedApiKeyFields(
            encrypted_key=base64.b64encode(b"replaced").decode("ascii"),
            salt=base64.b64encode(b"x" * 32).decode("ascii"),
            nonce=base64.b64encode(b"y" * 12).decode("ascii"),
            authentication_tag=base64.b64encode(b"z" * 16).decode("ascii"),
        )
        api_key_adapter.replace(llm_provider_id, replacement)
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            rows = (
                session.query(LLMProviderApiKeyModel)
                .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
                .all()
            )
            assert len(rows) == 1
            assert rows[0].encrypted_key == replacement.encrypted_key

    def test_replace_after_multiple_rows(self, api_key_adapter, llm_provider_id):
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            for suffix in ("1", "2"):
                session.add(
                    LLMProviderApiKeyModel(
                        llm_provider_id=llm_provider_id,
                        encrypted_key=f"k{suffix}",
                        salt=f"s{suffix}",
                        nonce=f"n{suffix}",
                        authentication_tag=f"t{suffix}",
                    )
                )
        api_key_adapter.replace(llm_provider_id, _fake_encrypted_fields())
        with sm.get_session() as session:
            rows = (
                session.query(LLMProviderApiKeyModel)
                .filter(LLMProviderApiKeyModel.llm_provider_id == llm_provider_id)
                .all()
            )
            assert len(rows) == 1
