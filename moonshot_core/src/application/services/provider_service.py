from typing import List, Optional
from application.ports.provider_repository import ProviderRepository
from domain.entities.provider_entity import ProviderEntity
from domain.entities.model_config_entity import ModelConfigEntity
from application.dto.provider_dto import ProviderDTO
from application.dto.model_config_dto import ModelConfigDTO
from application.services.sqlite_adapter import SQLiteAdapter
from domain.services.logger import configure_logger
from datetime import datetime


class ProviderService:
    """
    Service class for managing provider operations.
    
    This service provides high-level operations for managing providers,
    converting between database representations and domain entities.
    """
    
    def __init__(self, provider_repository: ProviderRepository):
        """
        Initialize the provider service.
        
        Args:
            provider_repository (ProviderRepository): The repository for provider data access.
        """
        self.provider_repository = provider_repository
        self.logger = configure_logger(__name__)
    
    def _provider_entity_to_dto(self, entity: ProviderEntity) -> ProviderDTO:
        """Convert ProviderEntity to ProviderDTO."""
        return ProviderDTO(
            id=entity.id,
            name=entity.name,
            defaultModel=entity.defaultModel,
            modelTextboxExplanation=entity.modelTextboxExplanation,
            defaultConfigPairs=entity.defaultConfigPairs,
            modelToken=entity.modelToken,
        )
    
    def _model_config_entity_to_dto(self, entity: ModelConfigEntity) -> ModelConfigDTO:
        """Convert ModelConfigEntity to ModelConfigDTO."""
        return ModelConfigDTO(
            id=entity.id,
            name=entity.name,
            modelname=entity.modelname,
            providerID=entity.providerID,
            savedConfigPairs=entity.savedConfigPairs,
            lastUpdated=entity.lastUpdated,
        )
    
    def _dto_to_provider_entity(self, dto: ProviderDTO) -> ProviderEntity:
        """Convert ProviderDTO to ProviderEntity."""
        return ProviderEntity(
            id=dto.id,
            name=dto.name,
            defaultModel=dto.defaultModel,
            modelTextboxExplanation=dto.modelTextboxExplanation,
            defaultConfigPairs=dto.defaultConfigPairs,
            modelToken=dto.modelToken,
        )
    
    def _dto_to_model_config_entity(self, dto: ModelConfigDTO) -> ModelConfigEntity:
        """Convert ModelConfigDTO to ModelConfigEntity."""
        # Ensure lastUpdated is present; if missing, use now
        last_updated = dto.lastUpdated if dto.lastUpdated else datetime.utcnow()
        return ModelConfigEntity(
            id=dto.id,
            name=dto.name,
            modelname=dto.modelname,
            providerID=dto.providerID,
            savedConfigPairs=dto.savedConfigPairs,
            lastUpdated=last_updated,
        )
    
    def get_provider_by_id(self, provider_id: str) -> Optional[ProviderDTO]:
        """
        Get a provider by its ID.
        
        Args:
            provider_id (str): The unique identifier of the provider.
            
        Returns:
            Optional[ProviderDTO]: The provider DTO if found, None otherwise.
        """
        self.logger.info(f"Getting provider by ID: {provider_id}")
        entity = self.provider_repository.get_provider_by_id(provider_id)
        return self._provider_entity_to_dto(entity) if entity else None
    
    def get_provider_by_name(self, name: str) -> Optional[ProviderDTO]:
        """
        Get a provider by its name.
        
        Args:
            name (str): The name of the provider.
            
        Returns:
            Optional[ProviderDTO]: The provider DTO if found, None otherwise.
        """
        self.logger.info(f"Getting provider by name: {name}")
        entity = self.provider_repository.get_provider_by_name(name)
        return self._provider_entity_to_dto(entity) if entity else None
    
    def list_providers(self) -> List[ProviderDTO]:
        """
        List all available providers.
        
        Returns:
            List[ProviderDTO]: A list of all provider DTOs.
        """
        self.logger.info("Listing all providers")
        entities = self.provider_repository.list_providers()
        return [self._provider_entity_to_dto(entity) for entity in entities]
    
    def add_provider(self, provider: ProviderDTO) -> ProviderDTO:
        """
        Add a new provider.
        
        Args:
            provider (ProviderDTO): The provider DTO to add.
            
        Returns:
            ProviderDTO: The added provider DTO with any generated fields.
        """
        self.logger.info(f"Adding provider: {provider.name}")
        entity = self._dto_to_provider_entity(provider)
        added_entity = self.provider_repository.add_provider(entity)
        return self._provider_entity_to_dto(added_entity)
    
    def update_provider(self, provider: ProviderDTO) -> ProviderDTO:
        """
        Update an existing provider.
        
        Args:
            provider (ProviderDTO): The provider DTO to update.
            
        Returns:
            ProviderDTO: The updated provider DTO.
        """
        self.logger.info(f"Updating provider: {provider.id}")
        entity = self._dto_to_provider_entity(provider)
        updated_entity = self.provider_repository.update_provider(entity)
        return self._provider_entity_to_dto(updated_entity)
    
    def delete_provider(self, provider_id: str) -> bool:
        """
        Delete a provider by its ID.
        
        Args:
            provider_id (str): The unique identifier of the provider to delete.
            
        Returns:
            bool: True if the provider was deleted, False otherwise.
        """
        self.logger.info(f"Deleting provider: {provider_id}")
        return self.provider_repository.delete_provider(provider_id)

    def get_model_configs_by_provider_id(self, provider_id: int) -> List[ModelConfigDTO]:
        """
        Get all model configurations associated with a provider ID.

        Args:
            provider_id (int): The numeric provider ID.

        Returns:
            List[ModelConfigDTO]: List of model configuration DTOs.
        """
        self.logger.info(f"Listing model configs by provider ID: {provider_id}")
        sqlite = SQLiteAdapter()
        entities = sqlite.get_all_model_config_entity(provider_id)
        return [self._model_config_entity_to_dto(entity) for entity in entities]

    def create_model_config(self, model_config: ModelConfigDTO) -> ModelConfigDTO:
        """
        Create a new model configuration.

        Args:
            model_config (ModelConfigDTO): The model configuration to create.

        Returns:
            ModelConfigDTO: The created model configuration DTO.
        """
        self.logger.info(f"Creating model config: {model_config.name}")
        entity = self._dto_to_model_config_entity(model_config)
        sqlite = SQLiteAdapter()
        created_entity = sqlite.add_model_config_entity(entity)
        return self._model_config_entity_to_dto(created_entity)

    def update_model_config(self, model_config: ModelConfigDTO) -> ModelConfigDTO:
        """
        Update an existing model configuration (matched by name).

        Args:
            model_config (ModelConfigDTO): The model configuration with updates.

        Returns:
            ModelConfigDTO: The updated model configuration DTO.
        """
        self.logger.info(f"Updating model config: {model_config.name}")
        entity = self._dto_to_model_config_entity(model_config)
        sqlite = SQLiteAdapter()
        updated_entity = sqlite.update_model_config_entity(entity)
        return self._model_config_entity_to_dto(updated_entity)

    def delete_model_config(self, config_id: str) -> bool:
        """
        Delete a model configuration (by ID or name).

        Args:
            config_id (str): The config ID or name to delete.

        Returns:
            bool: True if deleted, False otherwise.
        """
        self.logger.info(f"Deleting model config: {config_id}")
        sqlite = SQLiteAdapter()
        return sqlite.delete_model_config_entity(config_id)
