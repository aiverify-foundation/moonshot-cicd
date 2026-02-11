"""SQLAlchemy-based implementation of ProviderRepository."""

from typing import List, Optional, override
from application.ports.provider_repository import ProviderRepository
from domain.entities.provider_entity import ProviderEntity
from domain.services.logger import configure_logger
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.llm_provider_models import LLMProviderModel


class LLMProviderAdapter(ProviderRepository):
    """
    SQLAlchemy-based SQLite DB repository adapter implementing the ProviderRepository interface.
    """
    
    def __init__(self):
        """
        Initialize the SQLAlchemy repository adapter with the SessionManager.
        """
        self.session_manager = SessionManager()
        self.logger = configure_logger(__name__)
    
    def _model_to_entity(self, model: LLMProviderModel) -> ProviderEntity:
        """
        Convert a SQLAlchemy model to a ProviderEntity.
        
        Args:
            model (LLMProviderModel): The SQLAlchemy model.
            
        Returns:
            ProviderEntity: The converted provider entity.
        """
        return ProviderEntity(
            id=str(model.id),
            name=model.name,
            defaultModel="",  # Default values since DB doesn't store these
            modelTextboxExplanation="",
            defaultConfigPairs={},
            modelToken=""
        )
    
    @override
    def get_provider_by_id(self, provider_id: str) -> Optional[ProviderEntity]:
        """
        Get a LLM Provider entity by its ID.
        
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
            
            with self.session_manager.get_session() as session:
                model = session.query(LLMProviderModel).filter(
                    LLMProviderModel.id == db_id
                ).first()
                
                if model:
                    return self._model_to_entity(model)
                return None
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid provider ID format: {provider_id}, error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting provider by ID {provider_id}: {e}")
            return None
    
    @override
    def get_provider_by_name(self, name: str) -> Optional[ProviderEntity]:
        """
        Get a provider by its name.
        
        Args:
            name (str): The name of the provider.
            
        Returns:
            Optional[ProviderEntity]: The provider entity if found, None otherwise.
        """
        try:
            with self.session_manager.get_session() as session:
                model = session.query(LLMProviderModel).filter(
                    LLMProviderModel.name == name
                ).first()
                
                if model:
                    return self._model_to_entity(model)
                return None
        except Exception as e:
            self.logger.error(f"Error getting provider by name {name}: {e}")
            return None
    
    @override
    def list_providers(self) -> List[ProviderEntity]:
        """
        List all available providers.
        
        Returns:
            List[ProviderEntity]: A list of all provider entities.
        """
        try:
            with self.session_manager.get_session() as session:
                models: List[LLMProviderModel] = session \
                    .query(LLMProviderModel) \
                    .order_by(LLMProviderModel.name) \
                    .all()
                    
                return [self._model_to_entity(model) for model in models]
        except Exception as e:
            self.logger.error(f"LLMProviderAdapter.list_providers()::Error listing providers: {e}")
            raise e
    
    @override
    def add_provider(self, provider: ProviderEntity) -> ProviderEntity:
        """
        Add a new provider.
        
        Args:
            provider (ProviderEntity): The provider entity to add.
            
        Returns:
            ProviderEntity: The added provider entity with any generated fields.
        """
        try:
            with self.session_manager.get_session() as session:
                # Check if provider with same name already exists
                existing = session.query(LLMProviderModel).filter(
                    LLMProviderModel.name == provider.name
                ).first()
                
                if existing:
                    self.logger.warning(
                        f"Provider with name '{provider.name}' already exists"
                    )
                    return self._model_to_entity(existing)
                
                # Create new provider model
                new_model = LLMProviderModel(name=provider.name)
                session.add(new_model)
                session.flush()  # Flush to get the generated ID
                
                # Return the provider with the generated ID
                return ProviderEntity(
                    id=str(new_model.id),
                    name=new_model.name,
                    defaultModel=provider.defaultModel,
                    modelTextboxExplanation=provider.modelTextboxExplanation,
                    defaultConfigPairs=provider.defaultConfigPairs,
                    modelToken=provider.modelToken
                )
        except Exception as e:
            self.logger.error(f"Error adding provider: {e}")
            raise
    
    @override
    def update_provider(self, provider: ProviderEntity) -> ProviderEntity:
        """
        Update an existing provider.
        
        Args:
            provider (ProviderEntity): The provider entity to update.
            
        Returns:
            ProviderEntity: The updated provider entity.
        """
        try:
            if not provider.id.isdigit():
                self.logger.error(f"Invalid provider ID format: {provider.id}")
                raise ValueError(f"Invalid provider ID format: {provider.id}")
            
            db_id = int(provider.id)
            
            with self.session_manager.get_session() as session:
                model = session.query(LLMProviderModel).filter(
                    LLMProviderModel.id == db_id
                ).first()
                
                if not model:
                    self.logger.error(f"Provider with ID {provider.id} not found")
                    raise ValueError(f"Provider with ID {provider.id} not found")
                
                # Update the model
                model.name = provider.name
                session.flush()
                
                return provider
        except Exception as e:
            self.logger.error(f"Error updating provider: {e}")
            raise
    
    @override
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
            
            with self.session_manager.get_session() as session:
                model = session.query(LLMProviderModel).filter(
                    LLMProviderModel.id == db_id
                ).first()
                
                if not model:
                    self.logger.warning(f"Provider with ID {provider_id} not found")
                    return False
                
                session.delete(model)
                session.flush()
                
                return True
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid provider ID format: {provider_id}, error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting provider {provider_id}: {e}")
            return False

