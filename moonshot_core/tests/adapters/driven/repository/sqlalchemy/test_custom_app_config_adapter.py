from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from adapters.driven.repository.sqlalchemy.custom_app_config_adapter import (
    CustomAppConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root = Path(__file__).parent.parent.parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_custom_app_cfg.db"
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
def custom_app_adapter(test_db_env):
    return CustomAppAdapter()


@pytest.fixture
def custom_app_config_adapter(test_db_env):
    return CustomAppConfigAdapter()


class TestCustomAppConfigAdapter:
    def test_create_update_and_list(self, custom_app_adapter, custom_app_config_adapter):
        app = custom_app_adapter.add("API App")
        assert app.id is not None

        cfg = custom_app_config_adapter.create(
            app.id,
            "prod",
            {"api_url": "https://example.com", "api_type": "POST"},
        )
        assert cfg.id is not None
        assert cfg.name == "prod"
        assert cfg.custom_app_id == app.id

        params = custom_app_config_adapter.get_parameters(cfg.id)
        assert params == {"api_url": "https://example.com", "api_type": "POST"}

        configs = custom_app_config_adapter.list_by_app_id(app.id)
        assert len(configs) == 1
        assert configs[0].name == "prod"

        updated = custom_app_config_adapter.update(
            cfg.id,
            "prod-v2",
            {"api_url": "https://example.com/v2"},
        )
        assert updated.name == "prod-v2"
        assert custom_app_config_adapter.get_parameters(cfg.id) == {
            "api_url": "https://example.com/v2"
        }

    def test_create_requires_existing_app(self, custom_app_config_adapter):
        with pytest.raises(ValueError, match="No custom_app"):
            custom_app_config_adapter.create(999, "missing", {})
