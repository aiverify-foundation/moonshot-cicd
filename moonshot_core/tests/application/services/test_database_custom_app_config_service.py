from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.dto.custom_app_config_dto import (
    CreateCustomAppBody,
    CreateCustomAppConfigBody,
    UpdateCustomAppConfigBody,
)
from application.services.custom_app_config_secret_service import (
    CustomAppConfigSecretService,
)
from application.services.database_custom_app_config_service import (
    DatabaseCustomAppConfigService,
    DatabaseCustomAppService,
)


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root = Path(__file__).parent.parent.parent.parent
    db_path = (
        moonshot_core_root
        / "data"
        / "database"
        / "moonshot_pytest_custom_app_config_svc.db"
    )
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


class TestDatabaseCustomAppConfigServiceApiKeyConfigured:
    def test_api_key_configured_false_without_secret(self, test_db_env):
        sm = SessionManager.get_instance()
        app_svc = DatabaseCustomAppService(session_manager=sm)
        cfg_svc = DatabaseCustomAppConfigService(session_manager=sm)
        app = app_svc.create_app(CreateCustomAppBody(name="Test App"))
        assert app.id is not None

        created = cfg_svc.create(
            app.id,
            CreateCustomAppConfigBody(name="cfg", savedConfigPairs={"api_type": "POST"}),
        )
        assert created.api_key_configured is False

        listed = cfg_svc.list_configs(app.id)
        assert len(listed) == 1
        assert listed[0].api_key_configured is False

    def test_api_key_configured_true_after_set_secret(self, test_db_env):
        sm = SessionManager.get_instance()
        app_svc = DatabaseCustomAppService(session_manager=sm)
        cfg_svc = DatabaseCustomAppConfigService(session_manager=sm)
        secret_svc = CustomAppConfigSecretService(session_manager=sm)

        app = app_svc.create_app(CreateCustomAppBody(name="Secret App"))
        assert app.id is not None

        created = cfg_svc.create(
            app.id,
            CreateCustomAppConfigBody(name="cfg", savedConfigPairs={}),
        )
        assert created.id is not None
        assert created.api_key_configured is False

        secret_svc.set_secret(created.id, "api_key", "sk-test-secret")
        updated = cfg_svc.update(
            created.id,
            UpdateCustomAppConfigBody(name="cfg", savedConfigPairs={"api_url": "https://x"}),
        )
        assert updated.api_key_configured is True

        listed = cfg_svc.list_configs(app.id)
        assert listed[0].api_key_configured is True
