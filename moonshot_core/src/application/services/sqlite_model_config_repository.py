from typing import List, Optional, Dict, Any
from application.ports.model_config_repository import ModelConfigRepository
from domain.entities.model_config_entity import ModelConfigEntity
from application.services.sqlite_adapter import SQLiteAdapter
from domain.services.logger import configure_logger


class SQLiteModelConfigRepository(ModelConfigRepository):
    """
    SQLite-based implementation of the ModelConfigRepository interface.
    
    This repository uses the SQLiteAdapter to access model configuration data and converts
    database dictionaries to ModelConfigEntity objects.
    """
    
    def __init__(self, sqlite_adapter: SQLiteAdapter):
        """
        Initialize the SQLite model config repository.
        
        Args:
            sqlite_adapter (SQLiteAdapter): The SQLite adapter for database access.
        """
        self.sqlite_adapter = sqlite_adapter
        self.logger = configure_logger(__name__)
    
    def get_model_config_by_name(self, name: str) -> Optional[ModelConfigEntity]:
        """
        Get a model configuration by its config name.
        
        Args:
            name (str): The name in the config table.
            
        Returns:
            Optional[ModelConfigEntity]: The model configuration entity if found, None otherwise.
        """
        return self.sqlite_adapter.get_model_config_by_name(name)
    
    def get_model_configs_by_provider_id(self, provider_id: int) -> List[ModelConfigEntity]:
        """
        Get all model configurations associated with a given provider ID.

        Args:
            provider_id (int): The numeric provider ID in the database.

        Returns:
            List[ModelConfigEntity]: List of model configuration entities.
        """
        self.logger.info(f"Fetching model configs for provider_id={provider_id}")
        return self.sqlite_adapter.get_all_model_config_entity(provider_id)
    
    def add_model_config(self, model_config: ModelConfigEntity) -> ModelConfigEntity:
        """
        Add a new model configuration.
        
        Args:
            model_config (ModelConfigEntity): The model configuration entity to add.
            
        Returns:
            ModelConfigEntity: The added model configuration entity.
        """
        return self.sqlite_adapter.add_model_config_entity(model_config)
    
    def update_model_config(self, model_config: ModelConfigEntity) -> ModelConfigEntity:
        """
        Update an existing model configuration.
        
        Args:
            model_config (ModelConfigEntity): The model configuration entity to update.
            
        Returns:
            ModelConfigEntity: The updated model configuration entity.
        """
        return self.sqlite_adapter.update_model_config_entity(model_config)
    
    def delete_model_config(self, config_id: str) -> bool:
        """
        Delete a model configuration by its ID.
        
        Args:
            config_id (str): The unique identifier of the model configuration to delete.
            
        Returns:
            bool: True if the model configuration was deleted, False otherwise.
        """
        return self.sqlite_adapter.delete_model_config_entity(config_id)
