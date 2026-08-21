from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from adapters.driven.repository.sqlalchemy.custom_app_config_adapter import (
    CustomAppConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.custom_app_config_secret_service import (
    CustomAppConfigSecretService,
)
from application.services.database_custom_app_connector_config_service import (
    DatabaseCustomAppConnectorConfigService,
)


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root = Path(__file__).parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_custom_app_conn.db"
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


class TestDatabaseCustomAppConnectorConfigService:
    def test_build_connector_entity(self, test_db_env):
        sm = SessionManager.get_instance()
        app = CustomAppAdapter(sm).add("Together API")
        cfg = CustomAppConfigAdapter(sm).create(
            app.id,
            "prod",
            {
                "connector_adapter": "custom_api_connector_adapter",
                "api_type": "POST",
                "api_url": "https://api.example.com/v1/chat",
                "api_body": '{"messages": [{"role": "user", "content": "{{prompt}}"}]}',
            },
        )
        CustomAppConfigSecretService(session_manager=sm).set_secret(
            cfg.id, "api_key", "test-api-key"
        )

        entity = DatabaseCustomAppConnectorConfigService(session_manager=sm).build_connector_entity(
            custom_app_id=app.id,
            custom_app_config_id=cfg.id,
        )

        assert entity.connector_adapter == "custom_api_connector_adapter"
        assert entity.params["api_type"] == "POST"
        assert entity.params["api_url"] == "https://api.example.com/v1/chat"
        assert entity.params["api_key"] == "test-api-key"

    def test_rejects_mismatched_config(self, test_db_env):
        sm = SessionManager.get_instance()
        app_a = CustomAppAdapter(sm).add("App A")
        app_b = CustomAppAdapter(sm).add("App B")
        cfg_b = CustomAppConfigAdapter(sm).create(app_b.id, "cfg", {})

        with pytest.raises(ValueError, match="does not belong"):
            DatabaseCustomAppConnectorConfigService(session_manager=sm).build_connector_entity(
                custom_app_id=app_a.id,
                custom_app_config_id=cfg_b.id,
            )
