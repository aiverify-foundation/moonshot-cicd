from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.provider_entity import ProviderEntity


class ProviderRepository(ABC):
    """
    Abstract base class for provider repository implementations.
    
    This interface defines the contract for provider data access operations,
    ensuring consistent behavior across different repository implementations.
    """
    
    @abstractmethod
    def get_provider_by_id(self, provider_id: str) -> Optional[ProviderEntity]:
        """
        Get a provider by its ID.
        
        Args:
            provider_id (str): The unique identifier of the provider.
            
        Returns:
            Optional[ProviderEntity]: The provider entity if found, None otherwise.
        """
        pass
    
    @abstractmethod
    def get_provider_by_name(self, name: str) -> Optional[ProviderEntity]:
        """
        Get a provider by its name.
        
        Args:
            name (str): The name of the provider.
            
        Returns:
            Optional[ProviderEntity]: The provider entity if found, None otherwise.
        """
        pass
    
    @abstractmethod
    def list_providers(self) -> List[ProviderEntity]:
        """
        List all available providers.
        
        Returns:
            List[ProviderEntity]: A list of all provider entities.
        """
        pass
    
    @abstractmethod
    def add_provider(self, provider_name: str) -> ProviderEntity:
        """
        Add a new LLM Provider.
        
        Args:
            provider_name (str): The name of LLM Provider to add.
            
        Returns:
            ProviderEntity: The added provider entity with any generated fields.
        """
        pass
    
    @abstractmethod
    def update_provider(self, provider: ProviderEntity) -> ProviderEntity:
        """
        Update an existing provider.
        
        Args:
            provider (ProviderEntity): The provider entity to update.
            
        Returns:
            ProviderEntity: The updated provider entity.
        """
        pass
    
    @abstractmethod
    def delete_provider(self, provider_id: str) -> bool:
        """
        Delete a provider by its ID.
        
        Args:
            provider_id (str): The unique identifier of the provider to delete.
            
        Returns:
            bool: True if the provider was deleted, False otherwise.
        """
        pass
