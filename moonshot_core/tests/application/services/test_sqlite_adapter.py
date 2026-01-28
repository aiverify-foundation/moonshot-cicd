import pytest
import sqlite3
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from application.services.sqlite_adapter import SQLiteAdapter
from domain.entities.model_config_entity import ModelConfigEntity


def _create_test_schema(adapter):
    """Helper function to create test schema."""
    with adapter.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                last_update_dt DATE NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                UNIQUE(config_id, key),
                FOREIGN KEY(config_id) REFERENCES config(id)
            )
        """)
        conn.commit()


class TestSQLiteAdapter:
    """Test suite for SQLiteAdapter.add_model_config_entity method."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def sqlite_adapter(self, temp_db_path):
        """Create a SQLiteAdapter instance with a temporary database."""
        # Mock the initialization methods to avoid running migrations
        with patch.object(SQLiteAdapter, '_initialize_database'), \
             patch.object(SQLiteAdapter, '_initialize_provider_names'):
            adapter = SQLiteAdapter(db_path=temp_db_path)
            # Initialize the schema manually for testing
            _create_test_schema(adapter)
            return adapter

    @pytest.fixture
    def sample_model_config(self):
        """Create a sample ModelConfigEntity for testing."""
        return ModelConfigEntity(
            id="test_config_1",
            name="test_config_1",
            modelname="gpt-4",
            providerID="openai",
            savedConfigPairs={"temperature": "0.7", "max_tokens": "1000"},
            lastUpdated=datetime(2024, 1, 15)
        )

    @pytest.fixture
    def sample_model_config_no_params(self):
        """Create a ModelConfigEntity without parameters."""
        return ModelConfigEntity(
            id="test_config_2",
            name="test_config_2",
            modelname="gpt-3.5",
            providerID="openai",
            savedConfigPairs={},
            lastUpdated=datetime(2024, 1, 16)
        )

    def test_add_model_config_entity_create_new(self, sqlite_adapter, sample_model_config):
        """Test creating a new model config entity."""
        
        result = sqlite_adapter.add_model_config_entity(sample_model_config)
        
        assert result == sample_model_config
        
        # Verify config was created
        with sqlite_adapter.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM config WHERE name = ?", (sample_model_config.name,))
            row = cursor.fetchone()
            assert row is not None
            assert row["name"] == sample_model_config.name
            assert row["last_update_dt"] == sample_model_config.lastUpdated.strftime("%Y-%m-%d")
            
            # Verify parameters were saved
            cursor = conn.execute(
                "SELECT key, value FROM config_parameters WHERE config_id = ?",
                (row["id"],)
            )
            params = {row["key"]: row["value"] for row in cursor.fetchall()}
            assert params == sample_model_config.savedConfigPairs

    def test_add_model_config_entity_update_existing(self, sqlite_adapter, sample_model_config):
        """Test updating an existing model config entity."""
        
        # Create initial config
        sqlite_adapter.add_model_config_entity(sample_model_config)
        
        # Update with new data
        updated_config = ModelConfigEntity(
            id=sample_model_config.id,
            name=sample_model_config.name,
            modelname=sample_model_config.modelname,
            providerID=sample_model_config.providerID,
            savedConfigPairs={"temperature": "0.9", "max_tokens": "2000", "top_p": "0.95"},
            lastUpdated=datetime(2024, 1, 20)
        )
        
        result = sqlite_adapter.add_model_config_entity(updated_config)
        
        assert result == updated_config
        
        # Verify config was updated
        with sqlite_adapter.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM config WHERE name = ?", (updated_config.name,))
            row = cursor.fetchone()
            assert row["last_update_dt"] == updated_config.lastUpdated.strftime("%Y-%m-%d")
            
            # Verify parameters were updated
            cursor = conn.execute(
                "SELECT key, value FROM config_parameters WHERE config_id = ?",
                (row["id"],)
            )
            params = {row["key"]: row["value"] for row in cursor.fetchall()}
            assert params == updated_config.savedConfigPairs
            assert "top_p" in params
            assert params["temperature"] == "0.9"

    def test_add_model_config_entity_no_parameters(self, sqlite_adapter, sample_model_config_no_params):
        """Test creating a model config entity without parameters."""
        
        result = sqlite_adapter.add_model_config_entity(sample_model_config_no_params)
        
        assert result == sample_model_config_no_params
        
        # Verify config was created
        with sqlite_adapter.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM config WHERE name = ?", (sample_model_config_no_params.name,))
            row = cursor.fetchone()
            assert row is not None
            
            # Verify no parameters were saved
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM config_parameters WHERE config_id = ?",
                (row["id"],)
            )
            count = cursor.fetchone()["count"]
            assert count == 0

    def test_add_model_config_entity_update_parameters_to_empty(self, sqlite_adapter, sample_model_config):
        """Test updating a config to remove all parameters."""
        
        # Create initial config with parameters
        sqlite_adapter.add_model_config_entity(sample_model_config)
        
        # Update to remove all parameters
        updated_config = ModelConfigEntity(
            id=sample_model_config.id,
            name=sample_model_config.name,
            modelname=sample_model_config.modelname,
            providerID=sample_model_config.providerID,
            savedConfigPairs={},
            lastUpdated=datetime(2024, 1, 21)
        )
        
        result = sqlite_adapter.add_model_config_entity(updated_config)
        
        assert result == updated_config
        
        # Verify parameters were removed
        with sqlite_adapter.get_connection() as conn:
            cursor = conn.execute("SELECT id FROM config WHERE name = ?", (updated_config.name,))
            config_id = cursor.fetchone()["id"]
            
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM config_parameters WHERE config_id = ?",
                (config_id,)
            )
            count = cursor.fetchone()["count"]
            assert count == 0

    def test_add_model_config_entity_handles_empty_name(self, sqlite_adapter):
        """Test that method handles edge cases with empty name."""
        # Test with empty name - should still work but may not be a valid use case
        empty_name_config = ModelConfigEntity(
            id="",
            name="",
            modelname="gpt-4",
            providerID="openai",
            savedConfigPairs={},
            lastUpdated=datetime(2024, 1, 15)
        )
        
        # SQLite allows empty strings, so this should work
        result = sqlite_adapter.add_model_config_entity(empty_name_config)
        assert result == empty_name_config
        
        # Verify it was created
        with sqlite_adapter.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM config WHERE name = ?", ("",))
            row = cursor.fetchone()
            assert row is not None
