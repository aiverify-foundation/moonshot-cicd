from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from domain.entities.test_bundle_entity import TestBundleEntity
from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.benchmark_test_entity import BenchmarkTestEntity

class BenchmarkRepository(ABC):
    """
    Abstract base class for benchmark repository implementations.
    
    This interface defines the contract for benchmark data access operations including
    bundles, benchmark tests, and datasets. Implementations should provide concrete
    functionality for retrieving these entities from various storage backends.
    """
    
    def __init__(self, benchmark_source: Any = None):
        """
        Initialize the repository with optional test configurations.
        
        Args:
            benchmark_tests (Optional[Dict[str, List[BenchmarkTestEntity]]]): Test configurations to use
        """
        self.benchmark_source = benchmark_source
    
    @abstractmethod
    def get_bundle_by_id(self, bundle_id: str) -> TestBundleEntity:
        """
        Get a bundle by its ID.
        
        Args:
            bundle_id (str): The ID of the bundle to retrieve
            
        Returns:
            TestBundleEntity: The requested bundle
        """
        pass
    
    @abstractmethod
    def get_all_bundles(self) -> list[TestBundleEntity]:
        """
        Get all available bundles.
        
        Returns:
            list[TestBundleEntity]: List of all bundles
        """
        pass

    @abstractmethod
    def get_all_benchmark_tests(self) -> list[BenchmarkTestEntity]:
        """
        Get all available benchmark tests.
        
        Returns:
            list[BenchmarkTestEntity]: List of all benchmark tests
        """
        pass

    @abstractmethod
    def get_benchmark_test_by_id(self, benchmark_test_id: str) -> BenchmarkTestEntity:
        """
        Get a test config by its ID.
        
        Returns:
            BenchmarkTestEntity: The requested test config
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
