from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.model_config_entity import ModelConfigEntity


class ModelConfigRepository(ABC):
    """
    Abstract base class for model configuration repository implementations.

    This interface defines the contract for model configuration data access operations,
    ensuring consistent behavior across different repository implementations.
    """

    @abstractmethod
    def get_model_config_by_name(self, name: str) -> Optional[ModelConfigEntity]:
        """
        Get a model configuration by its config name.

        Args:
            name (str): The name in the config table.

        Returns:
            Optional[ModelConfigEntity]: The model configuration entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_model_config_by_id(self, config_id: str) -> Optional[ModelConfigEntity]:
        """
        Get a model configuration by its ID.

        Args:
            config_id (str): The unique identifier of the model configuration.

        Returns:
            Optional[ModelConfigEntity]: The model configuration entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def list_model_configs(self) -> List[ModelConfigEntity]:
        """
        List all available model configurations.

        Returns:
            List[ModelConfigEntity]: A list of all model configuration entities.
        """
        pass

    @abstractmethod
    def add_model_config(self, model_config: ModelConfigEntity) -> ModelConfigEntity:
        """
        Add a new model configuration.

        Args:
            model_config (ModelConfigEntity): The model configuration entity to add.

        Returns:
            ModelConfigEntity: The added model configuration entity.
        """
        pass

    @abstractmethod
    def update_model_config(self, model_config: ModelConfigEntity) -> ModelConfigEntity:
        """
        Update an existing model configuration.

        Args:
            model_config (ModelConfigEntity): The model configuration entity to update.

        Returns:
            ModelConfigEntity: The updated model configuration entity.
        """
        pass

    @abstractmethod
    def delete_model_config(self, config_id: str) -> bool:
        """
        Delete a model configuration by its ID.

        Args:
            config_id (str): The unique identifier of the model configuration to delete.

        Returns:
            bool: True if the model configuration was deleted, False otherwise.
        """
        pass
