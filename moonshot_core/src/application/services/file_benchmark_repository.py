from typing import Any, Dict, List, Optional
from application.ports.benchmark_repository import BenchmarkRepository
from application.ports.dataset_repository import DatasetRepository
from application.services.wrappers.bundle_entity_wrapper import TestBundleEntityWrapper
from domain.entities.test_config_entity import TestConfigEntity
from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.test_bundle_entity import TestBundleEntity
from domain.services.loader.file_loader import FileLoader, FileTypes
from application.services.utils import load_module
from domain.services.app_config import AppConfig
from domain.services.logger import configure_logger
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.benchmark_test_entity import BenchmarkTestEntity

class FileBenchmarkRepository(BenchmarkRepository):
    def __init__(self, benchmark_source: Any = None):
        """
        Initialize the file-based bundle repository.
        
        Args:
            test_configs (Optional[Dict[str, List[TestConfigEntity]]]): Test configurations to use.
                If None, will load from the default test config file.
        """
        super().__init__(benchmark_source)
        
        # Initialize logger
        self.logger = configure_logger(__name__)
        if self.benchmark_source is None:
            self.benchmark_source = AppConfig().get_benchmark_source()
        
        self.logger.info(f"Loading test config from {self.benchmark_source}")
        # tuple[Dict[str, List[TestBundleEntityWrapper]], Dict[str, List[BenchmarkTestEntityWrapper]]]
        # The first dictionary contains the bundle wrapper entities with their id as the key
        # The second dictionary contains the benchmark test wrapperentities with their id as the key
        self.test_configs = load_module(
            FileLoader,
            self.benchmark_source,
            FileTypes.DATA,
            "TEST_CONFIG_LOADED_MSG",
            "ERROR_LOADING_TEST_CONFIG"
        )

    def get_bundle_by_id(self, bundle_id: str) -> TestBundleEntity:
        """
        Get a bundle by its ID.
        
        Args:
            bundle_id (str): The ID of the bundle to retrieve
            
        Returns:
            TestBundleEntity: The requested bundle
            
        Raises:
            KeyError: If the bundle_id is not found
        """
        # Load test configs and bundles
        test_configs, bundles = self.test_configs
        
        if bundle_id not in bundles:
            self.logger.error(f"Bundle with ID '{bundle_id}' not found")
            raise KeyError(f"Bundle with ID '{bundle_id}' not found")
        
        bundle = bundles[bundle_id]
        test_list = []

        # Make sure to only include benchmark tests
        # Use test_names from the wrapper
        for test_name in bundle.test_names:
            if test_name in test_configs:
                test_wrapper = test_configs[test_name]
                # Get the dataset entity using the dataset name from the wrapper
                dataset_entity = self.get_dataset_by_id(test_wrapper.dataset_name)
                # Create BenchmarkTestEntity with the resolved dataset
                benchmark_test_entity = BenchmarkTestEntity(
                    id=test_wrapper.name,
                    name=test_wrapper.name,
                    dataset=dataset_entity,
                    metric=test_wrapper.metric,
                    description=test_wrapper.description
                )
                test_list.append(benchmark_test_entity)
        
        # Create and return the bundle with calculated metrics
        return TestBundleEntity(
            id=bundle_id,
            name=bundle.name,
            description=bundle.description,
            category=bundle.category,
            tests=test_list
        )
    
    def get_all_bundles(self) -> list[TestBundleEntity]:
        """
        Get all available bundles.
        
        Returns:
            list[TestBundleEntity]: List of all bundles
        """
        try:
            # Load test configs and bundles
            test_configs, bundles = self.test_configs
            
            bundle_list = []
            for bundle_id, bundle in bundles.items():
                test_list = []
                
                # Make sure to only include benchmark tests
                # Use test_names from the wrapper
                for test_name in bundle.test_names:
                    if test_name in test_configs:
                        test_wrapper = test_configs[test_name]
                        # Get the dataset entity using the dataset name from the wrapper
                        dataset_entity = self.get_dataset_by_id(test_wrapper.dataset_name)
                        # Create BenchmarkTestEntity with the resolved dataset
                        benchmark_test_entity = BenchmarkTestEntity(
                            id=test_wrapper.name,
                            name=test_wrapper.name,
                            dataset=dataset_entity,
                            metric=test_wrapper.metric,
                            description=test_wrapper.description,
                        )
                        test_list.append(benchmark_test_entity)
                
                # Create and return the bundle with calculated metrics
                bundle_entity = TestBundleEntity(
                    id=bundle_id,
                    name=bundle.name,
                    description=bundle.description,
                    category=bundle.category,
                    tests=test_list
                )
                bundle_list.append(bundle_entity)
            
            self.logger.info(f"Retrieved {len(bundle_list)} bundles")
            return bundle_list
            
        except Exception as e:
            self.logger.error(f"Error retrieving all bundles: {e}")
            raise
    
    def get_all_benchmark_tests(self) -> list[TestConfigEntity]:
        """
        Get all available test configurations.
        
        Returns:
            list[TestConfigEntity]: List of all test configurations
        """
        try:
            # Load test configs and bundles
            test_configs, bundles = self.test_configs
            
            test_config_list = []
            for test_id, test_config in test_configs.items():
                if test_config.type.value == "benchmark":
                    test_config_list.append(test_config)
            
            self.logger.info(f"Retrieved {len(test_config_list)} test configurations")
            return test_config_list
            
        except Exception as e:
            self.logger.error(f"Error retrieving all test configurations: {e}")
            raise

    def get_all_benchmark_tests(self) -> list[BenchmarkTestEntity]:
        """
        Get all available benchmark test entities.
        
        Returns:
            list[BenchmarkTestEntity]: List of all benchmark test entities
        """
        try:
            # Load test configs and bundles
            test_configs, bundles = self.test_configs
            
            benchmark_test_list = []
            for test_id, test_config in test_configs.items():
                if test_config.type.value == "benchmark":
                    dataset_entity = None
                    if test_config.dataset:
                        dataset_entity = self.get_dataset_by_id(test_config.dataset)
                    benchmark_test = BenchmarkTestEntity(
                        id=test_config.name,
                        name=test_config.name,
                        dataset=dataset_entity,
                        metric=test_config.metric
                    )
                    benchmark_test_list.append(benchmark_test)
            
            self.logger.info(f"Retrieved {len(benchmark_test_list)} benchmark test entities")
            return benchmark_test_list
            
        except Exception as e:
            self.logger.error(f"Error retrieving all benchmark test entities: {e}")
            raise
    
    def get_benchmark_test_by_id(self, test_id: str) -> BenchmarkTestEntity:
        """
        Get a benchmark test entity by its ID.
        
        Args:
            test_id (str): The ID of the benchmark test to retrieve
            
        Returns:
            BenchmarkTestEntity: The requested benchmark test entity
            
        Raises:
            KeyError: If the test_id is not found or is not a benchmark test
        """
        try:
            # Load test configs and bundles
            test_configs, bundles = self.test_configs
            
            if test_id not in test_configs:
                self.logger.error(f"Test configuration with ID '{test_id}' not found")
                raise KeyError(f"Test configuration with ID '{test_id}' not found")
            
            test_config = test_configs[test_id]
            if test_config.type.value != "benchmark":
                self.logger.error(f"Test configuration with ID '{test_id}' is not a benchmark test")
                raise KeyError(f"Test configuration with ID '{test_id}' is not a benchmark test")
            
            dataset_entity = None
            if test_config.dataset:
                dataset_entity = self.get_dataset_by_id(test_config.dataset)
            
            benchmark_test = BenchmarkTestEntity(
                id=test_config.name,
                name=test_config.name,
                dataset=dataset_entity,
                metric=test_config.metric
            )
            
            self.logger.info(f"Retrieved benchmark test entity: {benchmark_test.name}")
            return benchmark_test
            
        except Exception as e:
            self.logger.error(f"Error retrieving benchmark test entity '{test_id}': {e}")
            raise

    
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
        
