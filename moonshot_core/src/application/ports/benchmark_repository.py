from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from domain.entities.bundle_entity import BundleEntity
from domain.entities.test_config_entity import TestConfigEntity
from domain.entities.dataset_entity import DatasetEntity

class BenchmarkRepository(ABC):
    def __init__(self, benchmark_source: Any = None):
        """
        Initialize the repository with optional test configurations.
        
        Args:
            test_configs (Optional[Dict[str, List[TestConfigEntity]]]): Test configurations to use
        """
        self.benchmark_source = benchmark_source
    
    @abstractmethod
    def get_bundle_by_id(self, bundle_id: str) -> BundleEntity:
        """
        Get a bundle by its ID.
        
        Args:
            bundle_id (str): The ID of the bundle to retrieve
            
        Returns:
            BundleEntity: The requested bundle
        """
        pass
    
    @abstractmethod
    def get_all_bundles(self) -> list[BundleEntity]:
        """
        Get all available bundles.
        
        Returns:
            list[BundleEntity]: List of all bundles
        """
        pass

    @abstractmethod
    def get_all_test_configs(self) -> list[TestConfigEntity]:
        """
        Get all available bundles.
        
        Returns:
            list[BundleEntity]: List of all bundles
        """
        pass

    @abstractmethod
    def get_test_config_by_id(self, test_config_id: str) -> TestConfigEntity:
        """
        Get a test config by its ID.
        
        Returns:
            TestConfigEntity: The requested test config
        """
        pass

    @abstractmethod
    def get_dataset_by_id(self, dataset_id: str) -> DatasetEntity:
        """
        Get a dataset by its ID.
        
        Returns:
            DatasetEntity: The requested dataset
        """
        pass