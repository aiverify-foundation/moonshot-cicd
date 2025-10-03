from typing import Any, Dict, List, Optional
from application.ports.dataset_repository import DatasetRepository
from domain.entities.dataset_entity import DatasetEntity
from domain.services.loader.file_loader import FileLoader, FileTypes
from application.services.utils import load_module
from domain.services.app_config import AppConfig
from domain.services.logger import configure_logger

class FileDatasetRepository(DatasetRepository):
    def __init__(self, dataset_source: Any = None):
        """
        Initialize the file-based dataset repository.
        
        Args:
            dataset_source (Optional[Any]): Dataset source to use.
                If None, will use the default dataset path.
        """
        super().__init__(dataset_source)
        
        # Initialize logger
        self.logger = configure_logger(__name__)
        if self.dataset_source is None:
            self.dataset_source = AppConfig.DEFAULT_DATASETS_PATH
        
        self.logger.info(f"Initialized dataset repository with source: {self.dataset_source}")
    
    def get_dataset_by_id(self, dataset_id: str) -> DatasetEntity:
        """
        Get a dataset by its ID.
        
        Args:
            dataset_id (str): The ID of the dataset to retrieve
            
        Returns:
            DatasetEntity: The requested dataset
            
        Raises:
            Exception: If there is an error loading the dataset
        """
        try:
            self.logger.info(f"Loading dataset with ID: {dataset_id}")
            dataset = load_module(
                FileLoader,
                dataset_id,
                FileTypes.DATASET,
                "DATASET_LOADED_MSG",
                "ERROR_LOADING_DATASET"
            )
            self.logger.info(f"Successfully loaded dataset: {dataset.name}")
            return dataset
        except Exception as e:
            self.logger.error(f"Failed to load dataset '{dataset_id}': {e}")
            raise