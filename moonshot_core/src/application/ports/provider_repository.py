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
    