"""SQLite database adapter for moonshot-cicd."""

import sqlite3
import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime
from domain.entities.model_config_entity import ModelConfigEntity


class SQLiteAdapter:
    """SQLite database adapter for managing LLM providers, models, and configurations."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite adapter.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default path in data directory.
        """
        if db_path is None:
            # Default to moonshot_core/data/moonshot.db
            # Go up 3 levels from src/application/services/ to reach moonshot_core
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "moonshot.db")
        
        self.db_path = db_path
        self._initialize_database()
        self._initialize_provider_names()
    
    def _initialize_database(self) -> None:
        """Initialize the database with the required schema if it doesn't exist."""
        with self.get_connection() as conn:
            self._create_tables(conn)
            self._migrate_schema(conn)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all required tables based on the ERD schema."""
        
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create LLM_Provider table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_provider (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        
        # Create Model table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                llm_provider_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                create_dt DATE NOT NULL DEFAULT CURRENT_DATE,
                FOREIGN KEY (llm_provider_id) REFERENCES llm_provider(id),
                UNIQUE(llm_provider_id, name)
            )
        """)
        
        # Create Config table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                last_update_dt DATE NOT NULL DEFAULT CURRENT_DATE
            )
        """)
        
        # Create Model_Config junction table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                config_id INTEGER NOT NULL,
                last_run_dt DATE NOT NULL DEFAULT CURRENT_DATE,
                FOREIGN KEY (model_id) REFERENCES model(id),
                FOREIGN KEY (config_id) REFERENCES config(id),
                UNIQUE(model_id, config_id)
            )
        """)
        
        # Create Config_Parameters table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY (config_id) REFERENCES config(id),
                UNIQUE(config_id, key)
            )
        """)
        
        conn.commit()
    
    
    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        """Migrate database schema to add new columns if they don't exist."""
        # No migration needed for the original schema
        conn.commit()
    
    def _initialize_provider_names(self) -> None:
        """
        Initialize provider names from the providers.yaml file.
        Reads the YAML file and adds any missing provider names to the database.
        """
        try:
            # Get the path to the providers.yaml file
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
            providers_yaml_path = data_dir / "providers" / "providers.yaml"
            
            # Check if the YAML file exists
            if not providers_yaml_path.exists():
                print(f"Warning: Providers YAML file not found at {providers_yaml_path}")
                return
            
            # Read and parse the YAML file
            with open(providers_yaml_path, 'r', encoding='utf-8') as file:
                yaml_data = yaml.safe_load(file)
            
            # Extract provider names from the YAML data
            if not yaml_data or 'providers' not in yaml_data:
                print("Warning: No providers found in YAML file")
                return
            
            provider_names = []
            for provider in yaml_data['providers']:
                if 'name' in provider:
                    provider_names.append(provider['name'])
            
            # Add missing provider names to the database
            with self.get_connection() as conn:
                for provider_name in provider_names:
                    # Check if provider already exists
                    existing_provider = self.get_llm_provider_by_name(provider_name)
                    if not existing_provider:
                        try:
                            self.add_llm_provider(provider_name)
                            print(f"Added provider '{provider_name}' to database")
                        except sqlite3.IntegrityError:
                            # Provider might have been added by another process
                            print(f"Provider '{provider_name}' already exists in database")
                        except Exception as e:
                            print(f"Error adding provider '{provider_name}': {e}")
                    else:
                        print(f"Provider '{provider_name}' already exists in database")
                        
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
        except Exception as e:
            print(f"Error initializing provider names: {e}")
    
    def _get_config_parameters(self, config_id: str) -> Dict[str, str]:
        """Get all parameters for a model config."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT key, value FROM config_parameters WHERE config_id = ?",
                (config_id,)
            )
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def _save_config_parameters(self, config_id: str, parameters: Dict[str, str]) -> None:
        """Save parameters for a model config."""
        with self.get_connection() as conn:
            # Delete existing parameters
            conn.execute("DELETE FROM config_parameters WHERE config_id = ?", (config_id,))
            
            # Insert new parameters
            for key, value in parameters.items():
                conn.execute(
                    "INSERT INTO config_parameters (config_id, key, value) VALUES (?, ?, ?)",
                    (config_id, key, value)
                )
            conn.commit()

    def get_model_config_by_name(self, name: str) -> Optional[ModelConfigEntity]:
        """Get a ModelConfigEntity by its config name.

        The mapping follows:
        - id: config.name
        - name: config.name
        - modelname: model.name (from the model table)
        - providerID: llm_provider.name (provider name)
        - savedConfigPairs: key/value from config_parameters for the config_id
        - lastUpdated: config.last_update_dt
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT 
                    c.id AS config_id,
                    c.name AS config_name,
                    c.last_update_dt AS last_update_dt,
                    m.name AS model_name,
                    p.name AS provider_name
                FROM config c
                LEFT JOIN model_config mc ON mc.config_id = c.id
                LEFT JOIN model m ON m.id = mc.model_id
                LEFT JOIN llm_provider p ON p.id = m.llm_provider_id
                WHERE c.name = ?
                ORDER BY mc.last_run_dt DESC NULLS LAST
                LIMIT 1
                """,
                (name,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            config_id = str(row["config_id"]) if row["config_id"] is not None else None
            saved_params = self._get_config_parameters(config_id) if config_id is not None else {}

            last_updated_raw = row["last_update_dt"]
            # SQLite returns DATE as string YYYY-MM-DD; keep as date string or parse to datetime
            try:
                parsed_last_updated = datetime.strptime(last_updated_raw, "%Y-%m-%d") if isinstance(last_updated_raw, str) else last_updated_raw
            except Exception:
                parsed_last_updated = datetime.fromisoformat(last_updated_raw) if isinstance(last_updated_raw, str) else datetime.now()

            return ModelConfigEntity(
                id=row["config_name"],
                name=row["config_name"],
                modelname=row["model_name"] if row["model_name"] is not None else "",
                providerID=row["provider_name"] if row["provider_name"] is not None else "",
                savedConfigPairs=saved_params,
                lastUpdated=parsed_last_updated,
            )

    def add_model_config_entity(self, model_config: ModelConfigEntity) -> ModelConfigEntity:
        """
        Add a new model configuration entity.
        
        This method handles the complex relationship between config, model, and config_parameters tables.
        It will:
        1. Create or find the config entry
        2. Find the model by name and provider
        3. Create the model_config junction entry
        4. Save the config parameters
        
        Args:
            model_config (ModelConfigEntity): The model configuration entity to add.
            
        Returns:
            ModelConfigEntity: The added model configuration entity.
            
        Raises:
            ValueError: If model or provider not found
            sqlite3.IntegrityError: If config with same name already exists
        """
        with self.get_connection() as conn:
            try:
                # 1. Create or update the config entry
                cursor = conn.execute(
                    "INSERT OR REPLACE INTO config (name, last_update_dt) VALUES (?, ?)",
                    (model_config.name, model_config.lastUpdated.strftime("%Y-%m-%d"))
                )
                config_id = cursor.lastrowid
                
                # If INSERT OR REPLACE didn't return the ID, get it by name
                if config_id is None:
                    cursor = conn.execute("SELECT id FROM config WHERE name = ?", (model_config.name,))
                    row = cursor.fetchone()
                    config_id = row["id"] if row else None
                
                if config_id is None:
                    raise ValueError(f"Failed to create or find config with name: {model_config.name}")
                
                # 2. Find the model by name and provider
                if model_config.modelname and model_config.providerID:
                    # First find the provider
                    provider_cursor = conn.execute(
                        "SELECT id FROM llm_provider WHERE name = ?", 
                        (model_config.providerID,)
                    )
                    provider_row = provider_cursor.fetchone()
                    if not provider_row:
                        raise ValueError(f"Provider not found: {model_config.providerID}")
                    
                    provider_id = provider_row["id"]
                    
                    # Then find the model
                    model_cursor = conn.execute(
                        "SELECT id FROM model WHERE name = ? AND llm_provider_id = ?",
                        (model_config.modelname, provider_id)
                    )
                    model_row = model_cursor.fetchone()
                    if not model_row:
                        raise ValueError(f"Model not found: {model_config.modelname} for provider {model_config.providerID}")
                    
                    model_id = model_row["id"]
                    
                    # 3. Create or update the model_config junction entry
                    conn.execute(
                        """INSERT OR REPLACE INTO model_config (model_id, config_id, last_run_dt) 
                           VALUES (?, ?, ?)""",
                        (model_id, config_id, model_config.lastUpdated.strftime("%Y-%m-%d"))
                    )
                
                # 4. Save the config parameters
                if model_config.savedConfigPairs:
                    # Delete existing parameters
                    conn.execute("DELETE FROM config_parameters WHERE config_id = ?", (config_id,))
                    
                    # Insert new parameters
                    for key, value in model_config.savedConfigPairs.items():
                        conn.execute(
                            "INSERT INTO config_parameters (config_id, key, value) VALUES (?, ?, ?)",
                            (config_id, key, value)
                        )
                
                conn.commit()
                
                # Return the created entity (it should be the same as input)
                return model_config
                
            except Exception as e:
                conn.rollback()
                raise e

    def delete_model_config_entity(self, config_id: str) -> bool:
        """
        Delete a model configuration entity by config ID or name.
        
        Args:
            config_id (str): The config ID or name to delete.
            
        Returns:
            bool: True if the model configuration was deleted, False otherwise.
        """
        with self.get_connection() as conn:
            try:
                # First try to find the config by name (if config_id is actually a name)
                cursor = conn.execute("SELECT id FROM config WHERE name = ?", (config_id,))
                row = cursor.fetchone()
                
                if row:
                    actual_config_id = row["id"]
                else:
                    # Try to use config_id as an integer ID
                    try:
                        actual_config_id = int(config_id)
                    except ValueError:
                        return False
                
                # Delete from all related tables (in correct order due to foreign keys)
                conn.execute("DELETE FROM config_parameters WHERE config_id = ?", (actual_config_id,))
                conn.execute("DELETE FROM model_config WHERE config_id = ?", (actual_config_id,))
                cursor = conn.execute("DELETE FROM config WHERE id = ?", (actual_config_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
            except Exception:
                conn.rollback()
                return False

    def get_all_model_config_entity(self, provider_id: int) -> List[ModelConfigEntity]:
        """
        Get all model configurations for a specific provider.
        
        Args:
            provider_id (int): The provider ID.
            
        Returns:
            List[ModelConfigEntity]: List of model configuration entities.
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT 
                    c.id AS config_id,
                    c.name AS config_name,
                    c.last_update_dt AS last_update_dt,
                    m.name AS model_name,
                    p.name AS provider_name
                FROM config c
                LEFT JOIN model_config mc ON mc.config_id = c.id
                LEFT JOIN model m ON m.id = mc.model_id
                LEFT JOIN llm_provider p ON p.id = m.llm_provider_id
                WHERE p.id = ?
                ORDER BY c.name
                """,
                (provider_id,)
            )
            
            configs = []
            for row in cursor.fetchall():
                config_id = str(row["config_id"]) if row["config_id"] is not None else None
                saved_params = self._get_config_parameters(config_id) if config_id is not None else {}
                
                last_updated_raw = row["last_update_dt"]
                try:
                    parsed_last_updated = datetime.strptime(last_updated_raw, "%Y-%m-%d") if isinstance(last_updated_raw, str) else last_updated_raw
                except Exception:
                    parsed_last_updated = datetime.fromisoformat(last_updated_raw) if isinstance(last_updated_raw, str) else datetime.now()
                
                configs.append(ModelConfigEntity(
                    id=row["config_name"],
                    name=row["config_name"],
                    modelname=row["model_name"] if row["model_name"] is not None else "",
                    providerID=row["provider_name"] if row["provider_name"] is not None else "",
                    savedConfigPairs=saved_params,
                    lastUpdated=parsed_last_updated,
                ))
            
            return configs
    
    def update_model_config_entity(self, model_config: ModelConfigEntity) -> ModelConfigEntity:
        """
        Update a model configuration identified by its name. Provider association is preserved.

        This will:
        - Locate config by name (key)
        - Update config.last_update_dt
        - Update parameters in config_parameters
        - If a model association exists, keep the same provider and update model to the provided modelname (within same provider)
        - If no model association exists and provider is known (from input), associate to the model under that provider
        """
        with self.get_connection() as conn:
            try:
                # Find config by name
                cursor = conn.execute("SELECT id FROM config WHERE name = ?", (model_config.name,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Config not found by name: {model_config.name}")
                config_id = row["id"]

                # Update last_update_dt
                conn.execute(
                    "UPDATE config SET last_update_dt = ? WHERE id = ?",
                    (model_config.lastUpdated.strftime("%Y-%m-%d"), config_id)
                )

                # Determine existing provider association via current model_config
                cursor = conn.execute(
                    """
                    SELECT m.id AS model_id, p.id AS provider_id
                    FROM model_config mc
                    JOIN model m ON m.id = mc.model_id
                    JOIN llm_provider p ON p.id = m.llm_provider_id
                    WHERE mc.config_id = ?
                    LIMIT 1
                    """,
                    (config_id,)
                )
                assoc = cursor.fetchone()

                target_model_id = None
                target_provider_id = assoc["provider_id"] if assoc else None

                # If we have a desired model name, map it within the preserved provider
                if model_config.modelname:
                    if target_provider_id is None and model_config.providerID:
                        # No prior association; try using provided provider name
                        pcur = conn.execute("SELECT id FROM llm_provider WHERE name = ?", (model_config.providerID,))
                        prow = pcur.fetchone()
                        if prow:
                            target_provider_id = prow["id"]

                    if target_provider_id is not None:
                        mcur = conn.execute(
                            "SELECT id FROM model WHERE name = ? AND llm_provider_id = ?",
                            (model_config.modelname, target_provider_id)
                        )
                        mrow = mcur.fetchone()
                        if not mrow:
                            raise ValueError(
                                f"Model '{model_config.modelname}' not found under current provider"
                            )
                        target_model_id = mrow["id"]

                # Update or create model_config association if we resolved a model_id
                if target_model_id is not None:
                    conn.execute(
                        """
                        INSERT INTO model_config (model_id, config_id, last_run_dt)
                        VALUES (?, ?, ?)
                        ON CONFLICT(model_id, config_id) DO UPDATE SET last_run_dt=excluded.last_run_dt
                        """,
                        (target_model_id, config_id, model_config.lastUpdated.strftime("%Y-%m-%d"))
                    )

                # Refresh parameters
                conn.execute("DELETE FROM config_parameters WHERE config_id = ?", (config_id,))
                for key, value in (model_config.savedConfigPairs or {}).items():
                    conn.execute(
                        "INSERT INTO config_parameters (config_id, key, value) VALUES (?, ?, ?)",
                        (config_id, key, value)
                    )

                conn.commit()
                return model_config
            except Exception as e:
                conn.rollback()
                raise e
    
    def add_llm_provider(self, name: str) -> int:
        """
        Add a new LLM provider.
        
        Args:
            name: Name of the LLM provider
            
        Returns:
            ID of the created provider
            
        Raises:
            sqlite3.IntegrityError: If provider with same name already exists
        """
        with self.get_connection() as conn:
            cursor = conn.execute("INSERT INTO llm_provider (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid
    
    def get_llm_provider(self, provider_id: int) -> Optional[Dict[str, Any]]:
        """Get LLM provider by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM llm_provider WHERE id = ?", (provider_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_llm_provider_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get LLM provider by name."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM llm_provider WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_llm_providers(self) -> List[Dict[str, Any]]:
        """List all LLM providers."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM llm_provider ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def add_model(self, llm_provider_id: int, name: str) -> int:
        """
        Add a new model.
        
        Args:
            llm_provider_id: ID of the LLM provider
            name: Name of the model
            
        Returns:
            ID of the created model
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO model (llm_provider_id, name) VALUES (?, ?)",
                (llm_provider_id, name)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM model WHERE id = ?", (model_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_models(self, llm_provider_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all models, optionally filtered by provider."""
        with self.get_connection() as conn:
            if llm_provider_id:
                cursor = conn.execute(
                    "SELECT * FROM model WHERE llm_provider_id = ? ORDER BY name",
                    (llm_provider_id,)
                )
            else:
                cursor = conn.execute("SELECT * FROM model ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    

    
    def database_exists(self) -> bool:
        """Check if the database file exists."""
        return os.path.exists(self.db_path)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database."""
        info = {
            "path": self.db_path,
            "exists": self.database_exists(),
            "tables": []
        }
        
        if info["exists"]:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                info["tables"] = [row[0] for row in cursor.fetchall()]
        
        return info
