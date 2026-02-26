"""Tests for MoonshotConfigAdapter."""

import pytest
from pathlib import Path

from adapters.driven.repository.sqlalchemy.llm_provider_models import MoonshotConfigModel
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import MoonshotConfigAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager


@pytest.fixture(scope="function")
def test_db_path():
    """Create a temporary database path for testing."""
    moonshot_core_root: Path = Path(__file__).parent.parent.parent.parent.parent.parent
    db_path: Path = moonshot_core_root / "data" / "database" / "moonshot_pytest.db"

    if db_path.exists():
        db_path.unlink()

    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set up test database environment variable and reset SessionManager."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()

    yield

    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def moonshot_config_adapter(test_db_env):
    """Create a MoonshotConfigAdapter instance with real SessionManager."""
    return MoonshotConfigAdapter()


class TestMoonshotConfigAdapter:
    """Tests for MoonshotConfigAdapter."""

    def test_model_to_entity(self, moonshot_config_adapter):
        """Test conversion from SQLAlchemy model to MoonshotConfigEntity."""
        model = MoonshotConfigModel(id=1, key="foo", value="bar")
        entity = moonshot_config_adapter._model_to_entity(model)
        assert entity.id == 1
        assert entity.key == "foo"
        assert entity.value == "bar"

    def test_model_to_entity_null_value(self, moonshot_config_adapter):
        """Test conversion when value is None."""
        model = MoonshotConfigModel(id=2, key="baz", value=None)
        entity = moonshot_config_adapter._model_to_entity(model)
        assert entity.id == 2
        assert entity.key == "baz"
        assert entity.value is None

    def test_get_by_key_not_found(self, moonshot_config_adapter):
        """get_by_key returns None when key does not exist."""
        result = moonshot_config_adapter.get_by_key("nonexistent")
        assert result is None

    def test_set_insert_and_get_by_key(self, moonshot_config_adapter):
        """set inserts a new entry; get_by_key returns it."""
        saved = moonshot_config_adapter.set("my_key", "my_value")
        assert saved.key == "my_key"
        assert saved.value == "my_value"
        assert saved.id is not None

        found = moonshot_config_adapter.get_by_key("my_key")
        assert found is not None
        assert found.key == "my_key"
        assert found.value == "my_value"
        assert found.id == saved.id

    def test_set_update_existing(self, moonshot_config_adapter):
        """set updates value when key already exists."""
        moonshot_config_adapter.set("update_key", "first")
        updated = moonshot_config_adapter.set("update_key", "second")
        assert updated.key == "update_key"
        assert updated.value == "second"

        found = moonshot_config_adapter.get_by_key("update_key")
        assert found is not None
        assert found.value == "second"

    def test_set_null_value(self, moonshot_config_adapter):
        """set accepts None as value (e.g. to clear a config)."""
        moonshot_config_adapter.set("nullable_key", "something")
        saved = moonshot_config_adapter.set("nullable_key", None)
        assert saved.value is None
        found = moonshot_config_adapter.get_by_key("nullable_key")
        assert found is not None
        assert found.value is None

    def test_get_all_empty(self, moonshot_config_adapter):
        """get_all returns empty dict when no config entries exist."""
        # Use a fresh DB from test_db_env; only default LLM data may exist, moonshot_config is empty
        result = moonshot_config_adapter.get_all()
        assert isinstance(result, dict)
        # moonshot_config table is empty by default
        assert result == {}

    def test_get_all_with_entries(self, moonshot_config_adapter):
        """get_all returns all key-value pairs."""
        moonshot_config_adapter.set("a", "1")
        moonshot_config_adapter.set("b", "2")
        moonshot_config_adapter.set("c", None)

        result = moonshot_config_adapter.get_all()
        assert result == {"a": "1", "b": "2", "c": None}

    def test_delete_by_key_not_found(self, moonshot_config_adapter):
        """delete_by_key returns False when key does not exist."""
        deleted = moonshot_config_adapter.delete_by_key("nonexistent")
        assert deleted is False

    def test_delete_by_key_found(self, moonshot_config_adapter):
        """delete_by_key removes entry and returns True; get_by_key then returns None."""
        moonshot_config_adapter.set("to_delete", "value")
        deleted = moonshot_config_adapter.delete_by_key("to_delete")
        assert deleted is True

        found = moonshot_config_adapter.get_by_key("to_delete")
        assert found is None

    def test_roundtrip_set_get_all_delete(self, moonshot_config_adapter):
        """Roundtrip: set several, get_all, delete one, get_all again."""
        moonshot_config_adapter.set("k1", "v1")
        moonshot_config_adapter.set("k2", "v2")
        moonshot_config_adapter.set("k3", "v3")

        all_ = moonshot_config_adapter.get_all()
        assert all_ == {"k1": "v1", "k2": "v2", "k3": "v3"}

        moonshot_config_adapter.delete_by_key("k2")
        all_after = moonshot_config_adapter.get_all()
        assert all_after == {"k1": "v1", "k3": "v3"}
        assert moonshot_config_adapter.get_by_key("k2") is None
