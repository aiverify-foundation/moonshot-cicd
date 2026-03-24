##TODO: Remove this service and use the SQLAlchemy implementation instead
## THIS IS MARKED FOR DELETION
"""SQLite database adapter for moonshot-cicd."""

import sqlite3
import os
# import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime
from domain.entities.model_config_entity import ModelConfigEntity
# from alembic import command
# from alembic.config import Config
# from alembic import script
# from alembic.runtime.migration import MigrationContext
# from sqlalchemy import create_engine, inspect


class SQLiteAdapter:
    """SQLite database adapter for managing LLM providers, models, and configurations."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite adapter.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default path in data directory.
        """
        if db_path is None:
            # Default to moonshot_core/data/database/moonshot.db
            # Go up 3 levels from src/application/services/ to reach moonshot_core
            data_dir = Path(__file__).parent.parent.parent.parent / "data/database"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "moonshot.db")
        
        self.db_path = db_path
        self._initialize_database()
        # self._initialize_provider_names()
    
    def _initialize_database(self) -> None:
        """Initialize the database schema using Alembic migrations."""
        # self._run_alembic_migrations()
    
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
    
    # def _run_alembic_migrations(self) -> None:
    #     """Run Alembic migrations to initialize and update database schema."""
    #     # Get the path to alembic.ini (should be in moonshot_core/)
    #     moonshot_core_dir = Path(__file__).parent.parent.parent.parent
    #     alembic_ini_path = moonshot_core_dir / "alembic.ini"
        
    #     if not alembic_ini_path.exists():
    #         raise FileNotFoundError(f"Alembic config file not found at {alembic_ini_path}")
        
    #     # Create Alembic config
    #     alembic_cfg = Config(str(alembic_ini_path))
        
    #     # Update the database URL to use the actual database path
    #     # For SQLite absolute paths, use sqlite:/// (3 slashes)
    #     # Convert to absolute path if relative
    #     abs_db_path = os.path.abspath(self.db_path)
    #     db_url = f"sqlite:///{abs_db_path}"
    #     alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
    #     # Run migrations to head (latest version)
    #     try:
    #         command.upgrade(alembic_cfg, "head")
    #     except Exception as e:
    #         # If migration fails, it might be because tables already exist
    #         # In that case, we'll just log the error and continue
    #         # The application can still work if tables exist
    #         print(f"Warning: Alembic migration failed: {e}")
    #         print("Database may already be initialized. Continuing...")
    
    # def _initialize_provider_names(self) -> None:
    #     """
    #     Initialize provider names from the providers.yaml file.
    #     Reads the YAML file and adds any missing provider names to the database.
    #     """
    #     try:
    #         # Get the path to the providers.yaml file
    #         data_dir = Path(__file__).parent.parent.parent.parent / "data"
    #         providers_yaml_path = data_dir / "providers" / "providers.yaml"
            
    #         # Check if the YAML file exists
    #         if not providers_yaml_path.exists():
    #             print(f"Warning: Providers YAML file not found at {providers_yaml_path}")
    #             return
            
    #         # Read and parse the YAML file
    #         with open(providers_yaml_path, 'r', encoding='utf-8') as file:
    #             yaml_data = yaml.safe_load(file)
            
    #         # Extract provider names from the YAML data
    #         if not yaml_data or 'providers' not in yaml_data:
    #             print("Warning: No providers found in YAML file")
    #             return
            
    #         provider_names = []
    #         for provider in yaml_data['providers']:
    #             if 'name' in provider:
    #                 provider_names.append(provider['name'])
            
    #         # Add missing provider names to the database
    #         with self.get_connection() as conn:
    #             for provider_name in provider_names:
    #                 # Check if provider already exists
    #                 existing_provider = self.get_llm_provider_by_name(provider_name)
    #                 if not existing_provider:
    #                     try:
    #                         self.add_llm_provider(provider_name)
    #                         print(f"Added provider '{provider_name}' to database")
    #                     except sqlite3.IntegrityError:
    #                         # Provider might have been added by another process
    #                         print(f"Provider '{provider_name}' already exists in database")
    #                     except Exception as e:
    #                         print(f"Error adding provider '{provider_name}': {e}")
    #                 else:
    #                     print(f"Provider '{provider_name}' already exists in database")
                        
    #     except yaml.YAMLError as e:
    #         print(f"Error parsing YAML file: {e}")
    #     except Exception as e:
    #         print(f"Error initializing provider names: {e}")
    
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
        Create or update a model configuration entity.
        
        This method:
        1. Creates or updates the config entry
        2. Saves the config parameters
        
        Args:
            model_config (ModelConfigEntity): The model configuration entity to add/update.
            
        Returns:
            ModelConfigEntity: The added/updated model configuration entity.
        """
        with self.get_connection() as conn:
            try:
                # 1. Create or update config entry and get config_id
                conn.execute(
                    "INSERT INTO config (name, last_update_dt) VALUES (?, ?) "
                    "ON CONFLICT(name) DO UPDATE SET last_update_dt = excluded.last_update_dt",
                    (model_config.name, model_config.lastUpdated.strftime("%Y-%m-%d"))
                )
                cursor = conn.execute("SELECT id FROM config WHERE name = ?", (model_config.name,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Failed to create config with name: {model_config.name}")
                config_id = row["id"]
                
                # 2. Save config parameters
                # Always delete existing parameters first
                conn.execute("DELETE FROM config_parameters WHERE config_id = ?", (config_id,))
                
                # Then insert new parameters if any exist
                if model_config.savedConfigPairs:
                    for key, value in model_config.savedConfigPairs.items():
                        conn.execute(
                            "INSERT INTO config_parameters (config_id, key, value) VALUES (?, ?, ?) "
                            "ON CONFLICT(config_id, key) DO UPDATE SET value = excluded.value",
                            (config_id, key, value)
                        )
                
                conn.commit()
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
    
