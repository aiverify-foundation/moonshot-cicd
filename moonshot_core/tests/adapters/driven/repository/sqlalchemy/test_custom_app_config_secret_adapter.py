from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from adapters.driven.repository.sqlalchemy.custom_app_config_adapter import (
    CustomAppConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.custom_app_config_secret_adapter import (
    CustomAppConfigSecretAdapter,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (
    MoonshotConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.custom_app_config_secret_service import (
    CustomAppConfigSecretService,
)
from application.services.secrets_master_key_service import SecretsMasterKeyService
from domain.services.secret_encryption import encrypt_api_key


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root = Path(__file__).parent.parent.parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_custom_app_secret.db"
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
def secret_service(test_db_env):
    sm = SessionManager.get_instance()
    master = SecretsMasterKeyService(MoonshotConfigAdapter()).get_or_create_master_key_bytes()
    return CustomAppConfigSecretService(session_manager=sm), master


class TestCustomAppConfigSecretAdapter:
    def test_encrypt_store_and_decrypt(self, test_db_env, secret_service):
        service, master = secret_service
        app_adapter = CustomAppAdapter()
        config_adapter = CustomAppConfigAdapter()
        secret_adapter = CustomAppConfigSecretAdapter()

        app = app_adapter.add("Secret App")
        cfg = config_adapter.create(app.id, "default", {})

        payload = encrypt_api_key("super-secret-key", master)
        secret_adapter.replace(cfg.id, "api_key", payload)

        stored = secret_adapter.get_encrypted(cfg.id, "api_key")
        assert stored.encrypted_key == payload.encrypted_key

        service.set_secret(cfg.id, "api_key", "another-secret")
        assert service.get_decrypted_secret(cfg.id, "api_key") == "another-secret"
        assert secret_adapter.list_keys(cfg.id) == ["api_key"]
