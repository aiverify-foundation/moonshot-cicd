from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from adapters.driven.repository.sqlalchemy.llm_provider_models import CustomAppModel
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from domain.entities.custom_app_entity import CustomAppEntity


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root = Path(__file__).parent.parent.parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_custom_app.db"
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


class TestCustomAppAdapter:
    def test_model_to_entity(self, custom_app_adapter):
        model = CustomAppModel(id=1, name="My App")
        entity = custom_app_adapter._model_to_entity(model)
        assert entity == CustomAppEntity(id=1, name="My App")

    def test_list_empty_after_migrations(self, custom_app_adapter):
        assert custom_app_adapter.list_all() == []

    def test_add_and_list(self, custom_app_adapter):
        custom_app_adapter.add("App B")
        custom_app_adapter.add("App A")
        result = custom_app_adapter.list_all()
        assert len(result) == 2
        assert [e.name for e in result] == ["App A", "App B"]

    def test_get_by_id(self, custom_app_adapter):
        created = custom_app_adapter.add("Test App")
        assert created.id is not None
        fetched = custom_app_adapter.get_by_id(created.id)
        assert fetched is not None
        assert fetched.name == "Test App"
