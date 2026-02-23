from typing import List, Optional, Dict, Any
import json
from application.ports.provider_repository import ProviderRepository
from domain.entities.provider_entity import ProviderEntity
from application.services.sqlite_adapter import SQLiteAdapter
from domain.services.logger import configure_logger


class SQLiteProviderRepository(ProviderRepository):
    """
    SQLite-based implementation of the ProviderRepository interface.
    
    This repository uses the SQLiteAdapter to access provider data and converts
    database dictionaries to ProviderEntity objects.
    """
    
    def __init__(self, sqlite_adapter: SQLiteAdapter):
        """
        Initialize the SQLite provider repository.
        
        Args:
            sqlite_adapter (SQLiteAdapter): The SQLite adapter for database access.
        """
        self.sqlite_adapter = sqlite_adapter
        self.logger = configure_logger(__name__)
    
    def _dict_to_provider_entity(self, provider_dict: Dict[str, Any]) -> ProviderEntity:
        """
        Convert a database dictionary to a ProviderEntity.
        
        Args:
            provider_dict (Dict[str, Any]): The database dictionary.
            
        Returns:
            ProviderEntity: The converted provider entity.
        """
        return ProviderEntity(
            id=str(provider_dict["id"]),
            name=provider_dict["name"],
            defaultModel="",  # Default values since DB doesn't store these
            modelTextboxExplanation="",
            defaultConfigPairs={},
            modelToken=""
        )
    
    def _provider_entity_to_dict(self, provider: ProviderEntity) -> Dict[str, Any]:
        """
        Convert a ProviderEntity to a database dictionary.
        
        Args:
            provider (ProviderEntity): The provider entity.
            
        Returns:
            Dict[str, Any]: The database dictionary.
        """
        return {
            "id": int(provider.id) if provider.id.isdigit() else provider.id,
            "name": provider.name
        }
    
    def get_provider_by_id(self, provider_id: str) -> Optional[ProviderEntity]:
        """
        Get a provider by its ID.
        
        Args:
            provider_id (str): The unique identifier of the provider.
            
        Returns:
            Optional[ProviderEntity]: The provider entity if found, None otherwise.
        """
        try:
            # Convert string ID to int for database lookup
            if not provider_id.isdigit():
                self.logger.error(f"Invalid provider ID format: {provider_id}")
                return None
                
            db_id = int(provider_id)
            provider_dict = self.sqlite_adapter.get_llm_provider(db_id)
            
            if provider_dict:
                return self._dict_to_provider_entity(provider_dict)
            return None
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid provider ID format: {provider_id}, error: {e}")
            return None
    
    def get_provider_by_name(self, name: str) -> Optional[ProviderEntity]:
        """
        Get a provider by its name.
        
        Args:
            name (str): The name of the provider.
            
        Returns:
            Optional[ProviderEntity]: The provider entity if found, None otherwise.
        """
        provider_dict = self.sqlite_adapter.get_llm_provider_by_name(name)
        
        if provider_dict:
            return self._dict_to_provider_entity(provider_dict)
        return None
    
    def list_providers(self) -> List[ProviderEntity]:
        """
        List all available providers.
        
        Returns:
            List[ProviderEntity]: A list of all provider entities.
        """
        provider_dicts = self.sqlite_adapter.list_llm_providers()
        return [self._dict_to_provider_entity(provider_dict) for provider_dict in provider_dicts]
    
    def add_provider(self, provide_name: ProviderEntity) -> ProviderEntity:
        """
        Add a new provider.
        
        Args:
            provider (ProviderEntity): The provider entity to add.
            
        Returns:
            ProviderEntity: The added provider entity with any generated fields.
        """
        provider_id = self.sqlite_adapter.add_llm_provider(name=provide_name)
        
        # Return the provider with the generated ID
        return ProviderEntity(
            id=str(provider_id),
            name=provider.name,
            defaultModel=provider.defaultModel,
            modelTextboxExplanation=provider.modelTextboxExplanation,
            defaultConfigPairs=provider.defaultConfigPairs,
            modelToken=provider.modelToken
        )
    
    def update_provider(self, provider: ProviderEntity) -> ProviderEntity:
        """
        Update an existing provider.
        
        Args:
            provider (ProviderEntity): The provider entity to update.
            
        Returns:
            ProviderEntity: The updated provider entity.
        """
        provider_id = int(provider.id) if provider.id.isdigit() else provider.id
        
        with self.sqlite_adapter.get_connection() as conn:
            conn.execute(
                """UPDATE llm_provider 
                   SET name = ?
                   WHERE id = ?""",
                (provider.name, provider_id)
            )
            conn.commit()
        
        return provider
    
    def delete_provider(self, provider_id: str) -> bool:
        """
        Delete a provider by its ID.
        
        Args:
            provider_id (str): The unique identifier of the provider to delete.
            
        Returns:
            bool: True if the provider was deleted, False otherwise.
        """
        try:
            if not provider_id.isdigit():
                self.logger.error(f"Invalid provider ID format: {provider_id}")
                return False
                
            db_id = int(provider_id)
            
            with self.sqlite_adapter.get_connection() as conn:
                cursor = conn.execute("DELETE FROM llm_provider WHERE id = ?", (db_id,))
                conn.commit()
                return cursor.rowcount > 0
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid provider ID format: {provider_id}, error: {e}")
            return False
    
