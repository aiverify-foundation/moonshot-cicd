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
        self.session_manager = SessionManager.get_instance()
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
    def add_provider(self, provider_name: str) -> ProviderEntity:
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
                existing = session \
                    .query(LLMProviderModel) \
                    .filter(LLMProviderModel.name == provider_name) \
                    .first()
                
                if existing:
                    self.logger.warning(
                        f"Provider with name '{provider_name}' already exists"
                    )
                    return self._model_to_entity(existing)
                
                # Create new provider model
                new_model = LLMProviderModel(name=provider_name)
                session.add(new_model)
                session.flush()  # Flush to get the generated ID

                self.logger.info(f"Added provider: {new_model}")
                
                return self._model_to_entity(new_model)

        except Exception as e:
            self.logger.error(f"Error adding provider: {e}")
            raise
        
