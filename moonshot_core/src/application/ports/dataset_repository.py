from abc import ABC, abstractmethod
from typing import Any, Optional

from domain.entities.dataset_entity import DatasetEntity


class DatasetRepository(ABC):
    """
    Abstract base class for dataset repository implementations.
    
    This interface defines the contract for dataset data access operations.
    Implementations should provide concrete functionality for retrieving datasets.
    """

    def __init__(self, dataset_source: Optional[Any] = None):
        """
        Initialize the dataset repository.
        
        Args:
            dataset_source (Optional[Any]): Source configuration for dataset loading.
        """
        self.dataset_source = dataset_source

    @abstractmethod
    def get_dataset_by_id(self, dataset_id: str) -> DatasetEntity:
        """
        Retrieve a dataset by its identifier.
        
        Args:
            dataset_id (str): The unique identifier of the dataset to retrieve.
            
        Returns:
            DatasetEntity: The requested dataset entity.
            
        Raises:
            ValueError: If the dataset_id is invalid or malformed.
            FileNotFoundError: If the dataset file cannot be found.
            PermissionError: If access to the dataset is denied.
            Exception: For other dataset loading errors.
        """
        pass