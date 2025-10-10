import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List

from application.services.file_benchmark_repository import FileBenchmarkRepository
from application.services.wrappers.bundle_entity_wrapper import TestBundleEntityWrapper
from application.services.wrappers.benchmark_test_entity_wrapper import BenchmarkTestEntityWrapper
from domain.entities.test_config_entity import TestConfigEntity
from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.test_bundle_entity import TestBundleEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.services.enums.test_types import TestTypes
from domain.services.enums.file_types import FileTypes
from domain.services.loader.file_loader import FileLoader


class TestFileBenchmarkRepository:
    """Test class for FileBenchmarkRepository"""

    @pytest.fixture
    def mock_app_config(self):
        """Create a mock AppConfig"""
        mock_config = Mock()
        mock_config.get_benchmark_source.return_value = "test_config.yaml"
        return mock_config

    @pytest.fixture
    def sample_dataset_entity(self):
        """Create a sample DatasetEntity for testing"""
        return DatasetEntity(
            id="test_dataset_1",
            name="Test Dataset",
            description="A test dataset",
            examples=[{"input": "test", "output": "result"}],
            num_of_dataset_prompts=10,
            created_date="2023-12-01",
            reference="https://example.com",
            license="MIT"
        )

    @pytest.fixture
    def sample_test_config_entity(self):
        """Create a sample TestConfigEntity for testing"""
        return TestConfigEntity(
            name="test_benchmark",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset_1",
            metric={"name": "accuracy", "threshold": 0.8},
            description="Test benchmark",
            prompt="Test prompt"
        )

    @pytest.fixture
    def sample_benchmark_test_entity(self, sample_dataset_entity):
        """Create a sample BenchmarkTestEntity for testing"""
        return BenchmarkTestEntity(
            id="test_benchmark",
            name="test_benchmark",
            dataset=sample_dataset_entity,
            metric={"name": "accuracy", "threshold": 0.8},
            description="Test benchmark"
        )

    @pytest.fixture
    def sample_bundle_entity(self, sample_benchmark_test_entity):
        """Create a sample TestBundleEntity for testing"""
        return TestBundleEntity(
            id="test_bundle",
            name="test_bundle",
            description="Test bundle",
            category="test_category",
            tests=[sample_benchmark_test_entity]
        )

    @pytest.fixture
    def sample_bundle_wrapper(self):
        """Create a sample TestBundleEntityWrapper for testing"""
        wrapper = TestBundleEntityWrapper(
            name="test_bundle",
            description="Test bundle",
            tests=[],
            category="test_category",
            id="test_bundle"
        )
        wrapper.test_names = ["test_benchmark"]
        return wrapper

    @pytest.fixture
    def sample_test_wrapper(self):
        """Create a sample BenchmarkTestEntityWrapper for testing"""
        benchmark_test_entity = BenchmarkTestEntity(
            id="test_benchmark",
            name="test_benchmark",
            dataset=None,
            metric={"name": "accuracy", "threshold": 0.8},
            description="Test benchmark"
        )
        wrapper = BenchmarkTestEntityWrapper(benchmark_test_entity)
        wrapper.dataset_name = "test_dataset_1"
        return wrapper

    @pytest.fixture
    def mock_test_configs_data(self, sample_test_wrapper, sample_bundle_wrapper):
        """Create mock test configs data structure"""
        test_configs = {
            "test_benchmark": sample_test_wrapper
        }
        bundles = {
            "test_bundle": sample_bundle_wrapper
        }
        return test_configs, bundles

    @patch('application.services.file_benchmark_repository.AppConfig')
    @patch('application.services.file_benchmark_repository.load_module')
    def test_initialization_with_default_source(self, mock_load_module, mock_app_config_class, mock_test_configs_data):
        """Test FileBenchmarkRepository initialization with default benchmark source"""
        # Arrange
        mock_app_config = Mock()
        mock_app_config.get_benchmark_source.return_value = "default_config.yaml"
        mock_app_config_class.return_value = mock_app_config
        mock_load_module.return_value = mock_test_configs_data

        # Act
        repository = FileBenchmarkRepository()

        # Assert
        assert repository.benchmark_source == "default_config.yaml"
        mock_load_module.assert_called_once()
        mock_app_config.get_benchmark_source.assert_called_once()

    @patch('application.services.file_benchmark_repository.AppConfig')
    @patch('application.services.file_benchmark_repository.load_module')
    def test_initialization_with_custom_source(self, mock_load_module, mock_app_config_class, mock_test_configs_data):
        """Test FileBenchmarkRepository initialization with custom benchmark source"""
        # Arrange
        custom_source = "custom_config.yaml"
        mock_load_module.return_value = mock_test_configs_data

        # Act
        repository = FileBenchmarkRepository(custom_source)

        # Assert
        assert repository.benchmark_source == custom_source
        mock_load_module.assert_called_once_with(
            FileLoader,
            custom_source,
            FileTypes.DATA,
            "TEST_CONFIG_LOADED_MSG",
            "ERROR_LOADING_TEST_CONFIG"
        )

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_bundle_by_id_success(self, mock_load_module, mock_test_configs_data, sample_dataset_entity):
        """Test successful bundle retrieval by ID"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the get_dataset_by_id method
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_bundle_by_id("test_bundle")

        # Assert
        assert isinstance(result, TestBundleEntity)
        assert result.name == "test_bundle"
        assert result.description == "Test bundle"
        assert len(result.tests) == 1
        assert result.tests[0].name == "test_benchmark"

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_bundle_by_id_not_found(self, mock_load_module, mock_test_configs_data):
        """Test bundle retrieval when bundle is not found"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act & Assert
        with pytest.raises(KeyError, match="Bundle with ID 'nonexistent_bundle' not found"):
            repository.get_bundle_by_id("nonexistent_bundle")

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_bundle_by_id_with_missing_test_config(self, mock_load_module, sample_bundle_wrapper, sample_dataset_entity):
        """Test bundle retrieval when test config is missing"""
        # Arrange
        test_configs = {}
        bundles = {"test_bundle": sample_bundle_wrapper}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_bundle_by_id("test_bundle")

        # Assert
        assert isinstance(result, TestBundleEntity)
        assert result.name == "test_bundle"
        assert len(result.tests) == 0  # No tests because test config is missing

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_bundles_success(self, mock_load_module, mock_test_configs_data, sample_dataset_entity):
        """Test successful retrieval of all bundles"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_all_bundles()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TestBundleEntity)
        assert result[0].name == "test_bundle"

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_bundles_empty(self, mock_load_module):
        """Test retrieval of all bundles when none exist"""
        # Arrange
        mock_load_module.return_value = ({}, {})
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act
        result = repository.get_all_bundles()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_bundles_exception(self, mock_load_module, mock_test_configs_data):
        """Test exception handling in get_all_bundles"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the test_configs property to raise an exception when unpacking
        repository.test_configs = Mock()
        repository.test_configs.__iter__ = Mock(side_effect=Exception("Loading error"))

        # Act & Assert
        with pytest.raises(Exception):
            repository.get_all_bundles()

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_benchmark_tests_success(self, mock_load_module, sample_test_config_entity):
        """Test successful retrieval of all test configurations"""
        # Arrange
        test_configs = {"test_benchmark": sample_test_config_entity}
        bundles = {}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act
        result = repository.get_all_benchmark_tests()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TestConfigEntity)
        assert result[0].name == "test_benchmark"

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_benchmark_tests_filters_non_benchmark(self, mock_load_module, sample_dataset_entity):
        """Test that get_all_benchmark_tests filters out non-benchmark tests"""
        # Arrange
        benchmark_config = TestConfigEntity(
            name="benchmark_test",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset",
            metric={"name": "accuracy"}
        )
        scan_config = TestConfigEntity(
            name="scan_test",
            type=TestTypes.SCAN,
            dataset="test_dataset",
            metric={"name": "refusal"}
        )
        test_configs = {
            "benchmark_test": benchmark_config,
            "scan_test": scan_config
        }
        bundles = {}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_all_benchmark_tests()

        # Assert
        assert len(result) == 1
        assert result[0].name == "benchmark_test"
        assert result[0].dataset == sample_dataset_entity

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_benchmark_tests_exception(self, mock_load_module, mock_test_configs_data):
        """Test exception handling in get_all_benchmark_tests"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the test_configs property to raise an exception when unpacking
        repository.test_configs = Mock()
        repository.test_configs.__iter__ = Mock(side_effect=Exception("Loading error"))

        # Act & Assert
        with pytest.raises(Exception):
            repository.get_all_benchmark_tests()

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_benchmark_tests_success(self, mock_load_module, sample_test_config_entity, sample_dataset_entity):
        """Test successful retrieval of all benchmark test entities"""
        # Arrange
        test_configs = {"test_benchmark": sample_test_config_entity}
        bundles = {}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_all_benchmark_tests()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], BenchmarkTestEntity)
        assert result[0].name == "test_benchmark"
        assert result[0].dataset == sample_dataset_entity

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_benchmark_tests_with_none_dataset(self, mock_load_module):
        """Test get_all_benchmark_tests with test config having no dataset"""
        # Arrange
        test_config = TestConfigEntity(
            name="test_no_dataset",
            type=TestTypes.BENCHMARK,
            dataset="",
            metric={"name": "accuracy"}
        )
        test_configs = {"test_no_dataset": test_config}
        bundles = {}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act
        result = repository.get_all_benchmark_tests()

        # Assert
        assert len(result) == 1
        assert result[0].dataset is None

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_all_benchmark_tests_exception(self, mock_load_module, mock_test_configs_data):
        """Test exception handling in get_all_benchmark_tests"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the test_configs property to raise an exception when unpacking
        repository.test_configs = Mock()
        repository.test_configs.__iter__ = Mock(side_effect=Exception("Loading error"))

        # Act & Assert
        with pytest.raises(Exception):
            repository.get_all_benchmark_tests()

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_benchmark_test_by_id_success(self, mock_load_module, sample_test_config_entity, sample_dataset_entity):
        """Test successful benchmark test retrieval by ID"""
        # Arrange
        test_configs = {"test_benchmark": sample_test_config_entity}
        bundles = {}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_benchmark_test_by_id("test_benchmark")

        # Assert
        assert isinstance(result, BenchmarkTestEntity)
        assert result.name == "test_benchmark"
        assert result.dataset == sample_dataset_entity
        assert result.metric == {"name": "accuracy", "threshold": 0.8}

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_benchmark_test_by_id_not_found(self, mock_load_module):
        """Test benchmark test retrieval when test is not found"""
        # Arrange
        mock_load_module.return_value = ({}, {})
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act & Assert
        with pytest.raises(KeyError, match="Test configuration with ID 'nonexistent_test' not found"):
            repository.get_benchmark_test_by_id("nonexistent_test")

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_benchmark_test_by_id_not_benchmark(self, mock_load_module):
        """Test benchmark test retrieval when test is not a benchmark test"""
        # Arrange
        scan_config = TestConfigEntity(
            name="scan_test",
            type=TestTypes.SCAN,
            dataset="test_dataset",
            metric={"name": "refusal"}
        )
        test_configs = {"scan_test": scan_config}
        bundles = {}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act & Assert
        with pytest.raises(KeyError, match="Test configuration with ID 'scan_test' is not a benchmark test"):
            repository.get_benchmark_test_by_id("scan_test")

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_benchmark_test_by_id_exception(self, mock_load_module, mock_test_configs_data):
        """Test exception handling in get_benchmark_test_by_id"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the test_configs property to raise an exception when unpacking
        repository.test_configs = Mock()
        repository.test_configs.__iter__ = Mock(side_effect=Exception("Loading error"))

        # Act & Assert
        with pytest.raises(Exception):
            repository.get_benchmark_test_by_id("test_id")


    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_benchmark_test_by_id_not_found(self, mock_load_module):
        """Test test config retrieval when config is not found"""
        # Arrange
        mock_load_module.return_value = ({}, {})
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act & Assert
        with pytest.raises(KeyError, match="Test configuration with ID 'nonexistent_config' not found"):
            repository.get_benchmark_test_by_id("nonexistent_config")

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_benchmark_test_by_id_exception(self, mock_load_module, mock_test_configs_data):
        """Test exception handling in get_benchmark_test_by_id"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the test_configs property to raise an exception when unpacking
        repository.test_configs = Mock()
        repository.test_configs.__iter__ = Mock(side_effect=Exception("Loading error"))

        # Act & Assert
        with pytest.raises(Exception):
            repository.get_benchmark_test_by_id("test_id")

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_dataset_by_id_success(self, mock_load_module, sample_dataset_entity):
        """Test successful dataset retrieval by ID"""
        # Arrange
        mock_load_module.return_value = sample_dataset_entity
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act
        result = repository.get_dataset_by_id("test_dataset_1")

        # Assert
        assert isinstance(result, DatasetEntity)
        assert result.id == "test_dataset_1"
        assert result.name == "Test Dataset"
        mock_load_module.assert_called_with(
            FileLoader,
            "test_dataset_1",
            FileTypes.DATASET,
            "DATASET_LOADED_MSG",
            "ERROR_LOADING_DATASET"
        )

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_dataset_by_id_exception(self, mock_load_module, mock_test_configs_data):
        """Test exception handling in get_dataset_by_id"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the load_module call for dataset loading to raise an exception
        with patch('application.services.file_benchmark_repository.load_module') as mock_dataset_load:
            mock_dataset_load.side_effect = Exception("Dataset loading error")
            
            # Act & Assert
            with pytest.raises(Exception, match="Dataset loading error"):
                repository.get_dataset_by_id("test_dataset")

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_dataset_by_id_with_nonexistent_dataset(self, mock_load_module, mock_test_configs_data):
        """Test get_dataset_by_id with nonexistent dataset"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the load_module call for dataset loading to raise FileNotFoundError
        with patch('application.services.file_benchmark_repository.load_module') as mock_dataset_load:
            mock_dataset_load.side_effect = FileNotFoundError("Dataset not found")
            
            # Act & Assert
            with pytest.raises(FileNotFoundError, match="Dataset not found"):
                repository.get_dataset_by_id("nonexistent_dataset")

    @patch('application.services.file_benchmark_repository.load_module')
    def test_multiple_bundles_with_different_tests(self, mock_load_module, sample_dataset_entity):
        """Test handling multiple bundles with different test configurations"""
        # Arrange
        test_wrapper1 = BenchmarkTestEntityWrapper(
            BenchmarkTestEntity(
                id="test1",
                name="test1",
                dataset=None,
                metric={"name": "accuracy"},
                description="Test 1"
            )
        )
        test_wrapper1.dataset_name = "dataset1"

        test_wrapper2 = BenchmarkTestEntityWrapper(
            BenchmarkTestEntity(
                id="test2",
                name="test2",
                dataset=None,
                metric={"name": "refusal"},
                description="Test 2"
            )
        )
        test_wrapper2.dataset_name = "dataset2"

        bundle_wrapper1 = TestBundleEntityWrapper(name="bundle1", description="Bundle 1", tests=[], category="test_category", id="bundle1")
        bundle_wrapper1.test_names = ["test1"]

        bundle_wrapper2 = TestBundleEntityWrapper(name="bundle2", description="Bundle 2", tests=[], category="test_category", id="bundle2")
        bundle_wrapper2.test_names = ["test2"]

        test_configs = {
            "test1": test_wrapper1,
            "test2": test_wrapper2
        }
        bundles = {
            "bundle1": bundle_wrapper1,
            "bundle2": bundle_wrapper2
        }
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_all_bundles()

        # Assert
        assert len(result) == 2
        assert result[0].name == "bundle1"
        assert result[1].name == "bundle2"
        assert len(result[0].tests) == 1
        assert len(result[1].tests) == 1
        assert result[0].tests[0].name == "test1"
        assert result[1].tests[0].name == "test2"

    @patch('application.services.file_benchmark_repository.load_module')
    def test_bundle_with_multiple_tests(self, mock_load_module, sample_dataset_entity):
        """Test bundle with multiple test configurations"""
        # Arrange
        test_wrapper1 = BenchmarkTestEntityWrapper(
            BenchmarkTestEntity(
                id="test1",
                name="test1",
                dataset=None,
                metric={"name": "accuracy"},
                description="Test 1"
            )
        )
        test_wrapper1.dataset_name = "dataset1"

        test_wrapper2 = BenchmarkTestEntityWrapper(
            BenchmarkTestEntity(
                id="test2",
                name="test2",
                dataset=None,
                metric={"name": "refusal"},
                description="Test 2"
            )
        )
        test_wrapper2.dataset_name = "dataset2"

        bundle_wrapper = TestBundleEntityWrapper(name="multi_bundle", description="Multi bundle", tests=[], category="test_category", id="multi_bundle")
        bundle_wrapper.test_names = ["test1", "test2"]

        test_configs = {
            "test1": test_wrapper1,
            "test2": test_wrapper2
        }
        bundles = {
            "multi_bundle": bundle_wrapper
        }
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_bundle_by_id("multi_bundle")

        # Assert
        assert result.name == "multi_bundle"
        assert len(result.tests) == 2
        assert result.tests[0].name == "test1"
        assert result.tests[1].name == "test2"

    @patch('application.services.file_benchmark_repository.load_module')
    def test_edge_case_empty_strings(self, mock_load_module):
        """Test edge cases with empty strings"""
        # Arrange
        test_config = TestConfigEntity(
            name="",
            type=TestTypes.BENCHMARK,
            dataset="",
            metric={},
            description="",
            prompt=""
        )
        test_configs = {"": test_config}
        bundles = {}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act
        result = repository.get_all_benchmark_tests()

        # Assert
        assert len(result) == 1
        assert result[0].name == ""
        assert result[0].dataset is None  # Empty dataset string results in None

    @patch('application.services.file_benchmark_repository.load_module')
    def test_complex_metric_structure(self, mock_load_module, sample_dataset_entity):
        """Test handling of complex metric structures"""
        # Arrange
        complex_metric = {
            "name": "complex_metric",
            "threshold": 0.85,
            "weights": {"precision": 0.6, "recall": 0.4},
            "categories": ["category1", "category2"],
            "nested": {"config": {"value": 42}}
        }
        
        test_config = TestConfigEntity(
            name="complex_test",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset",
            metric=complex_metric,
            description="Complex test"
        )
        test_configs = {"complex_test": test_config}
        bundles = {}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        result = repository.get_benchmark_test_by_id("complex_test")

        # Assert
        assert result.metric == complex_metric
        assert result.metric["nested"]["config"]["value"] == 42

    @patch('application.services.file_benchmark_repository.load_module')
    def test_large_dataset_handling(self, mock_load_module):
        """Test handling of large datasets"""
        # Arrange
        large_examples = [{"example": i} for i in range(1000)]
        large_dataset = DatasetEntity(
            id="large_dataset",
            name="Large Dataset",
            description="Large dataset for testing",
            examples=large_examples,
            num_of_dataset_prompts=1000
        )
        mock_load_module.return_value = large_dataset
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act
        result = repository.get_dataset_by_id("large_dataset")

        # Assert
        assert len(result.examples) == 1000
        assert result.num_of_dataset_prompts == 1000

    @patch('application.services.file_benchmark_repository.load_module')
    def test_repository_logging(self, mock_load_module, mock_test_configs_data, sample_dataset_entity):
        """Test that repository properly logs operations"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the get_dataset_by_id method to return a proper dataset entity
        repository.get_dataset_by_id = Mock(return_value=sample_dataset_entity)

        # Act
        repository.get_all_bundles()

        # Assert
        # Verify that logger was configured
        assert hasattr(repository, 'logger')
        assert repository.logger is not None

    @patch('application.services.file_benchmark_repository.load_module')
    def test_error_logging_on_exception(self, mock_load_module, mock_test_configs_data):
        """Test that errors are properly logged when exceptions occur"""
        # Arrange
        mock_load_module.return_value = mock_test_configs_data
        repository = FileBenchmarkRepository("test_config.yaml")
        
        # Mock the test_configs property to raise an exception when unpacking
        repository.test_configs = Mock()
        repository.test_configs.__iter__ = Mock(side_effect=Exception("Test error"))

        # Act & Assert
        with pytest.raises(Exception):
            repository.get_all_bundles()

    @pytest.mark.parametrize("dataset_id", ["dataset1", "dataset2", "dataset3"])
    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_dataset_by_id_parametrized(self, mock_load_module, dataset_id):
        """Test get_dataset_by_id with different dataset IDs"""
        # Arrange
        dataset = DatasetEntity(
            id=dataset_id,
            name=f"Dataset {dataset_id}",
            description=f"Description for {dataset_id}",
            examples=[]
        )
        mock_load_module.return_value = dataset
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act
        result = repository.get_dataset_by_id(dataset_id)

        # Assert
        assert result.id == dataset_id
        assert result.name == f"Dataset {dataset_id}"

    @pytest.mark.parametrize("bundle_id", ["bundle1", "bundle2", "bundle3"])
    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_bundle_by_id_parametrized(self, mock_load_module, bundle_id):
        """Test get_bundle_by_id with different bundle IDs"""
        # Arrange
        bundle_wrapper = TestBundleEntityWrapper(name=bundle_id, description=f"Description for {bundle_id}", tests=[], category="test_category", id=bundle_id)
        test_configs = {}
        bundles = {bundle_id: bundle_wrapper}
        mock_load_module.return_value = (test_configs, bundles)
        repository = FileBenchmarkRepository("test_config.yaml")

        # Act
        result = repository.get_bundle_by_id(bundle_id)

        # Assert
        assert result.name == bundle_id
        assert result.description == f"Description for {bundle_id}"
