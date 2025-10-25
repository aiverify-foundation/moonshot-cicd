import os
from datetime import datetime
from typing import List, Optional

from domain.entities.model_config_entity import ModelConfigEntity
from application.ports.model_config_repository import ModelConfigRepository
from adapters.file_format.yaml_adapter import YamlAdapter
from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)


class FileModelConfigRepository(ModelConfigRepository):
    """
    File-based implementation of ModelConfigRepository that reads from YAML files.
    
    This implementation loads model configurations from a YAML file and provides
    read-only access. Write operations (create, update, delete) are not supported
    and will raise NotImplementedError.
    """
    
    def __init__(self, config_file_path: str):
        """
        Initialize the file-based model config repository.
        
        Args:
            config_file_path (str): Path to the YAML configuration file.
        """
        self.config_file_path = config_file_path
        self.yaml_adapter = YamlAdapter()
        self._configs: List[ModelConfigEntity] = []
        self._load_configs()
    
    def _load_configs(self) -> None:
        """
        Load model configurations from the YAML file.
        
        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the YAML file is invalid or empty.
        """
        if not os.path.exists(self.config_file_path):
            logger.error(f"Configuration file not found: {self.config_file_path}")
            raise FileNotFoundError(f"Configuration file not found: {self.config_file_path}")
        
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            data = self.yaml_adapter.deserialize(content)
            if not data:
                logger.error(f"Failed to deserialize YAML content from {self.config_file_path}")
                raise ValueError(f"Invalid or empty YAML file: {self.config_file_path}")
            
            self._configs = []
            for config_name, config_data in data.items():
                try:
                    # Convert lastUpdated string to datetime if it's a string
                    last_updated = config_data.get('lastUpdated')
                    if isinstance(last_updated, str):
                        last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    elif last_updated is None:
                        last_updated = datetime.now()
                    
                    config_entity = ModelConfigEntity(
                        id=config_data.get('id', ''),
                        name=config_data.get('name', ''),
                        modelname=config_data.get('modelname', ''),
                        providerID=config_data.get('providerID', ''),
                        savedConfigPairs=config_data.get('savedConfigPairs', {}),
                        lastUpdated=last_updated
                    )
                    self._configs.append(config_entity)
                    logger.debug(f"Loaded model config: {config_name} -> {config_entity.name}")
                    
                except Exception as e:
                    logger.error(f"Error loading config '{config_name}': {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(self._configs)} model configurations from {self.config_file_path}")
            
        except Exception as e:
            logger.error(f"Error loading configurations from {self.config_file_path}: {e}")
            raise ValueError(f"Failed to load configurations: {e}")
    
    def get_model_config_by_name(self, name: str) -> Optional[ModelConfigEntity]:
        """
        Get a model configuration by its config name.
        
        Args:
            name (str): The name in the config table.
            
        Returns:
            Optional[ModelConfigEntity]: The model configuration entity if found, None otherwise.
        """
        for config in self._configs:
            if config.name == name:
                logger.debug(f"Found model config by name: {name}")
                return config
        
        logger.debug(f"Model config not found by name: {name}")
        return None
    
    def get_model_config_by_id(self, config_id: str) -> Optional[ModelConfigEntity]:
        """
        Get a model configuration by its ID.
        
        Args:
            config_id (str): The unique identifier of the model configuration.
            
        Returns:
            Optional[ModelConfigEntity]: The model configuration entity if found, None otherwise.
        """
        for config in self._configs:
            if config.id == config_id:
                logger.debug(f"Found model config by ID: {config_id}")
                return config
        
        logger.debug(f"Model config not found by ID: {config_id}")
        return None
    
    def list_model_configs(self) -> List[ModelConfigEntity]:
        """
        List all available model configurations.
        
        Returns:
            List[ModelConfigEntity]: A list of all model configuration entities.
        """
        logger.debug(f"Returning {len(self._configs)} model configurations")
        return self._configs.copy()  # Return a copy to prevent external modification
    
    def add_model_config(self, model_config: ModelConfigEntity) -> ModelConfigEntity:
        """
        Add a new model configuration.
        
        This operation is not supported in file-based repository.
        
        Args:
            model_config (ModelConfigEntity): The model configuration entity to add.
            
        Returns:
            ModelConfigEntity: The added model configuration entity.
            
        Raises:
            NotImplementedError: This operation is not supported in file-based repository.
        """
        logger.error("Add operation not supported in file-based model config repository")
        raise NotImplementedError("Add operation not supported in file-based model config repository")
    
    def update_model_config(self, model_config: ModelConfigEntity) -> ModelConfigEntity:
        """
        Update an existing model configuration.
        
        This operation is not supported in file-based repository.
        
        Args:
            model_config (ModelConfigEntity): The model configuration entity to update.
            
        Returns:
            ModelConfigEntity: The updated model configuration entity.
            
        Raises:
            NotImplementedError: This operation is not supported in file-based model config repository.
        """
        logger.error("Update operation not supported in file-based model config repository")
        raise NotImplementedError("Update operation not supported in file-based model config repository")
    
    def delete_model_config(self, config_id: str) -> bool:
        """
        Delete a model configuration by its ID.
        
        This operation is not supported in file-based repository.
        
        Args:
            config_id (str): The unique identifier of the model configuration to delete.
            
        Returns:
            bool: True if the model configuration was deleted, False otherwise.
            
        Raises:
            NotImplementedError: This operation is not supported in file-based model config repository.
        """
        logger.error("Delete operation not supported in file-based model config repository")
        raise NotImplementedError("Delete operation not supported in file-based model config repository")
