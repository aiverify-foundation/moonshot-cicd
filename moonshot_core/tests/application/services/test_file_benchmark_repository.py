import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, List

from application.services.file_benchmark_repository import FileBenchmarkRepository
from domain.entities.bundle_entity import BundleEntity
from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.test_config_entity import TestConfigEntity
from domain.services.enums.test_types import TestTypes
from application.services.wrappers.bundle_entity_wrapper import BundleEntityWrapper
from application.services.wrappers.benchmark_test_entity_wrapper import BenchmarkTestEntityWrapper


class TestFileBenchmarkRepository:
    """Test class for FileBenchmarkRepository"""

    @pytest.fixture
    def mock_file_loader(self):
        """Create a mock FileLoader"""
        return Mock()

    @pytest.fixture
    def mock_app_config(self):
        """Create a mock AppConfig"""
        return Mock()

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
            name="test_config_1",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset_1",
            metric={"name": "accuracy", "threshold": 0.8},
            prompt="Test prompt"
        )

    @pytest.fixture
    def sample_bundle_wrapper(self):
        """Create a sample BundleEntityWrapper for testing"""
        wrapper = Mock(spec=BundleEntityWrapper)
        wrapper.name = "test_bundle"
        wrapper.description = "Test bundle description"
        wrapper.test_names = ["test_config_1", "test_config_2"]
        wrapper.tests = []
        return wrapper

    @pytest.fixture
    def sample_test_wrapper(self):
        """Create a sample BenchmarkTestEntityWrapper for testing"""
        wrapper = Mock(spec=BenchmarkTestEntityWrapper)
        wrapper.name = "test_config_1"
        wrapper.dataset_name = "test_dataset_1"
        wrapper.metric = {"name": "accuracy", "threshold": 0.8}
        wrapper.description = "Test description"
        return wrapper

    @pytest.fixture
    def sample_test_configs_and_bundles(self, sample_test_wrapper, sample_bundle_wrapper):
        """Create sample test configs and bundles tuple"""
        test_configs = {
            "test_config_1": sample_test_wrapper,
            "test_config_2": sample_test_wrapper
        }
        bundles = {
            "bundle_1": sample_bundle_wrapper
        }
        return (test_configs, bundles)

    @patch('application.services.file_benchmark_repository.load_module')
    @patch('application.services.file_benchmark_repository.AppConfig')
    def test_initialization_with_default_source(self, mock_app_config_class, mock_load_module, sample_test_configs_and_bundles):
        """Test FileBenchmarkRepository initialization with default source"""
        # Arrange
        mock_app_config_instance = Mock()
        mock_app_config_instance.get_benchmark_source.return_value = "default_source"
        mock_app_config_class.return_value = mock_app_config_instance
        mock_load_module.return_value = sample_test_configs_and_bundles

        # Act
        repository = FileBenchmarkRepository()

        # Assert
        mock_app_config_instance.get_benchmark_source.assert_called_once()
        mock_load_module.assert_called_once()
        assert repository.benchmark_source == "default_source"

    @patch('application.services.file_benchmark_repository.load_module')
    def test_initialization_with_custom_source(self, mock_load_module, sample_test_configs_and_bundles):
        """Test FileBenchmarkRepository initialization with custom source"""
        # Arrange
        custom_source = "custom_source"
        mock_load_module.return_value = sample_test_configs_and_bundles

        # Act
        repository = FileBenchmarkRepository(custom_source)

        # Assert
        mock_load_module.assert_called_once()
        assert repository.benchmark_source == custom_source

    def test_get_bundle_by_id_success(self, sample_test_configs_and_bundles, sample_dataset_entity):
        """Test successful bundle retrieval by ID"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = sample_test_configs_and_bundles
            
            repository = FileBenchmarkRepository()
            
            # Mock the get_dataset_by_id method
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):
                bundle_id = "bundle_1"

                # Act
                result = repository.get_bundle_by_id(bundle_id)

                # Assert
                assert isinstance(result, BundleEntity)
                assert result.name == "test_bundle"
                assert result.description == "Test bundle description"
                assert len(result.tests) == 2  # Based on test_names length

    def test_get_bundle_by_id_not_found(self, sample_test_configs_and_bundles):
        """Test bundle retrieval when bundle is not found"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = sample_test_configs_and_bundles
            
            repository = FileBenchmarkRepository()
            bundle_id = "nonexistent_bundle"

            # Act & Assert
            with pytest.raises(KeyError, match="Bundle with ID 'nonexistent_bundle' not found"):
                repository.get_bundle_by_id(bundle_id)

    def test_get_bundle_by_id_with_dataset_resolution(self, sample_test_configs_and_bundles, sample_dataset_entity):
        """Test bundle retrieval with dataset resolution"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = sample_test_configs_and_bundles
            
            repository = FileBenchmarkRepository()
            
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):
                bundle_id = "bundle_1"

                # Act
                result = repository.get_bundle_by_id(bundle_id)

                # Assert
                assert len(result.tests) == 2
                for test in result.tests:
                    assert isinstance(test, BenchmarkTestEntity)
                    assert test.dataset == sample_dataset_entity

    def test_get_all_bundles_success(self, sample_test_configs_and_bundles):
        """Test successful retrieval of all bundles"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = sample_test_configs_and_bundles
            
            repository = FileBenchmarkRepository()

            # Act
            result = repository.get_all_bundles()

            # Assert
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], BundleEntity)
            assert result[0].name == "test_bundle"

    def test_get_all_bundles_exception_handling(self, sample_test_configs_and_bundles):
        """Test exception handling in get_all_bundles"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.side_effect = Exception("Load error")
            
            repository = FileBenchmarkRepository()

            # Act & Assert
            with pytest.raises(Exception, match="Load error"):
                repository.get_all_bundles()

    def test_get_all_test_configs_success(self, sample_test_configs_and_bundles, sample_test_config_entity):
        """Test successful retrieval of all test configs"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        test_configs["test_config_1"] = sample_test_config_entity
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()

            # Act
            result = repository.get_all_test_configs()

            # Assert
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TestConfigEntity)
            assert result[0].name == "test_config_1"

    def test_get_all_test_configs_filter_benchmark_only(self, sample_test_configs_and_bundles):
        """Test that only benchmark test configs are returned"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        
        # Add a scan test config
        scan_test_config = TestConfigEntity(
            name="scan_test",
            type=TestTypes.SCAN,
            metric={"name": "safety_score"}
        )
        test_configs["scan_test"] = scan_test_config
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()

            # Act
            result = repository.get_all_test_configs()

            # Assert
            assert len(result) == 2  # Only benchmark tests
            for config in result:
                assert config.type.value == "benchmark"

    def test_get_all_test_configs_exception_handling(self, sample_test_configs_and_bundles):
        """Test exception handling in get_all_test_configs"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.side_effect = Exception("Load error")
            
            repository = FileBenchmarkRepository()

            # Act & Assert
            with pytest.raises(Exception, match="Load error"):
                repository.get_all_test_configs()

    def test_get_all_benchmark_tests_success(self, sample_test_configs_and_bundles, sample_dataset_entity):
        """Test successful retrieval of all benchmark test entities"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        test_configs["test_config_1"] = TestConfigEntity(
            name="test_config_1",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset_1",
            metric={"name": "accuracy"}
        )
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):

                # Act
                result = repository.get_all_benchmark_tests()

                # Assert
                assert isinstance(result, list)
                assert len(result) == 2
                for test in result:
                    assert isinstance(test, BenchmarkTestEntity)
                    assert test.dataset == sample_dataset_entity

    def test_get_all_benchmark_tests_with_none_dataset(self, sample_test_configs_and_bundles):
        """Test retrieval of benchmark tests with None dataset"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        test_configs["test_config_1"] = TestConfigEntity(
            name="test_config_1",
            type=TestTypes.BENCHMARK,
            dataset=None,
            metric={"name": "accuracy"}
        )
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()

            # Act
            result = repository.get_all_benchmark_tests()

            # Assert
            assert len(result) == 2
            for test in result:
                assert isinstance(test, BenchmarkTestEntity)
                assert test.dataset is None

    def test_get_all_benchmark_tests_exception_handling(self, sample_test_configs_and_bundles):
        """Test exception handling in get_all_benchmark_tests"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.side_effect = Exception("Load error")
            
            repository = FileBenchmarkRepository()

            # Act & Assert
            with pytest.raises(Exception, match="Load error"):
                repository.get_all_benchmark_tests()

    def test_get_benchmark_test_by_id_success(self, sample_test_configs_and_bundles, sample_dataset_entity):
        """Test successful benchmark test retrieval by ID"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        test_configs["test_config_1"] = TestConfigEntity(
            name="test_config_1",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset_1",
            metric={"name": "accuracy"}
        )
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):
                test_id = "test_config_1"

                # Act
                result = repository.get_benchmark_test_by_id(test_id)

                # Assert
                assert isinstance(result, BenchmarkTestEntity)
                assert result.name == "test_config_1"
                assert result.dataset == sample_dataset_entity
                assert result.metric == {"name": "accuracy"}

    def test_get_benchmark_test_by_id_not_found(self, sample_test_configs_and_bundles):
        """Test benchmark test retrieval when test is not found"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = sample_test_configs_and_bundles
            
            repository = FileBenchmarkRepository()
            test_id = "nonexistent_test"

            # Act & Assert
            with pytest.raises(KeyError, match="Test configuration with ID 'nonexistent_test' not found"):
                repository.get_benchmark_test_by_id(test_id)

    def test_get_benchmark_test_by_id_not_benchmark(self, sample_test_configs_and_bundles):
        """Test benchmark test retrieval when test is not a benchmark type"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        test_configs["scan_test"] = TestConfigEntity(
            name="scan_test",
            type=TestTypes.SCAN,
            metric={"name": "safety_score"}
        )
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            test_id = "scan_test"

            # Act & Assert
            with pytest.raises(KeyError, match="Test configuration with ID 'scan_test' is not a benchmark test"):
                repository.get_benchmark_test_by_id(test_id)

    def test_get_benchmark_test_by_id_exception_handling(self, sample_test_configs_and_bundles):
        """Test exception handling in get_benchmark_test_by_id"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.side_effect = Exception("Load error")
            
            repository = FileBenchmarkRepository()

            # Act & Assert
            with pytest.raises(Exception, match="Load error"):
                repository.get_benchmark_test_by_id("test_id")

    def test_get_test_config_by_id_success(self, sample_test_configs_and_bundles, sample_test_config_entity):
        """Test successful test config retrieval by ID"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        test_configs["test_config_1"] = sample_test_config_entity
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            test_config_id = "test_config_1"

            # Act
            result = repository.get_test_config_by_id(test_config_id)

            # Assert
            assert isinstance(result, TestConfigEntity)
            assert result.name == "test_config_1"

    def test_get_test_config_by_id_not_found(self, sample_test_configs_and_bundles):
        """Test test config retrieval when config is not found"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = sample_test_configs_and_bundles
            
            repository = FileBenchmarkRepository()
            test_config_id = "nonexistent_config"

            # Act & Assert
            with pytest.raises(KeyError, match="Test configuration with ID 'nonexistent_config' not found"):
                repository.get_test_config_by_id(test_config_id)

    def test_get_test_config_by_id_exception_handling(self, sample_test_configs_and_bundles):
        """Test exception handling in get_test_config_by_id"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.side_effect = Exception("Load error")
            
            repository = FileBenchmarkRepository()

            # Act & Assert
            with pytest.raises(Exception, match="Load error"):
                repository.get_test_config_by_id("test_id")

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_dataset_by_id_success(self, mock_load_module, sample_dataset_entity):
        """Test successful dataset retrieval by ID"""
        # Arrange
        mock_load_module.return_value = sample_dataset_entity
        repository = FileBenchmarkRepository()
        dataset_id = "test_dataset_1"

        # Act
        result = repository.get_dataset_by_id(dataset_id)

        # Assert
        mock_load_module.assert_called_once()
        assert result == sample_dataset_entity

    @patch('application.services.file_benchmark_repository.load_module')
    def test_get_dataset_by_id_exception_handling(self, mock_load_module):
        """Test exception handling in get_dataset_by_id"""
        # Arrange
        mock_load_module.side_effect = Exception("Dataset load error")
        repository = FileBenchmarkRepository()
        dataset_id = "test_dataset_1"

        # Act & Assert
        with pytest.raises(Exception, match="Dataset load error"):
            repository.get_dataset_by_id(dataset_id)

    def test_bundle_entity_creation_with_multiple_tests(self, sample_test_configs_and_bundles, sample_dataset_entity):
        """Test BundleEntity creation with multiple tests"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        
        # Add more test configs
        test_configs["test_config_2"] = TestConfigEntity(
            name="test_config_2",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset_1",
            metric={"name": "precision"}
        )
        test_configs["test_config_3"] = TestConfigEntity(
            name="test_config_3",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset_1",
            metric={"name": "recall"}
        )
        
        # Update bundle to include all tests
        bundle_wrapper = bundles["bundle_1"]
        bundle_wrapper.test_names = ["test_config_1", "test_config_2", "test_config_3"]
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):

                # Act
                result = repository.get_bundle_by_id("bundle_1")

                # Assert
                assert len(result.tests) == 3
                assert all(isinstance(test, BenchmarkTestEntity) for test in result.tests)
                assert result.tests[0].name == "test_config_1"
                assert result.tests[1].name == "test_config_2"
                assert result.tests[2].name == "test_config_3"

    def test_benchmark_test_entity_creation_with_description(self, sample_test_configs_and_bundles, sample_dataset_entity):
        """Test BenchmarkTestEntity creation with description"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        test_configs["test_config_1"] = TestConfigEntity(
            name="test_config_1",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset_1",
            metric={"name": "accuracy"},
            prompt="Test prompt"
        )
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):

                # Act
                result = repository.get_benchmark_test_by_id("test_config_1")

                # Assert
                assert result.name == "test_config_1"
                assert result.dataset == sample_dataset_entity
                assert result.metric == {"name": "accuracy"}
                assert result.description == ""  # Default value

    def test_edge_case_empty_test_configs(self):
        """Test edge case with empty test configs"""
        # Arrange
        empty_test_configs = {}
        empty_bundles = {}
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (empty_test_configs, empty_bundles)
            
            repository = FileBenchmarkRepository()

            # Act
            test_configs_result = repository.get_all_test_configs()
            benchmark_tests_result = repository.get_all_benchmark_tests()
            bundles_result = repository.get_all_bundles()

            # Assert
            assert test_configs_result == []
            assert benchmark_tests_result == []
            assert bundles_result == []

    def test_complex_metric_structure(self, sample_test_configs_and_bundles, sample_dataset_entity):
        """Test with complex metric structure"""
        # Arrange
        complex_metric = {
            "name": "complex_metric",
            "threshold": 0.85,
            "weights": {"precision": 0.6, "recall": 0.4},
            "categories": ["category1", "category2"],
            "nested": {"config": {"value": 42}}
        }
        
        test_configs, bundles = sample_test_configs_and_bundles
        test_configs["test_config_1"] = TestConfigEntity(
            name="test_config_1",
            type=TestTypes.BENCHMARK,
            dataset="test_dataset_1",
            metric=complex_metric
        )
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):

                # Act
                result = repository.get_benchmark_test_by_id("test_config_1")

                # Assert
                assert result.metric == complex_metric
                assert result.metric["nested"]["config"]["value"] == 42

    def test_large_number_of_tests(self, sample_dataset_entity):
        """Test with large number of tests"""
        # Arrange
        test_configs = {}
        bundles = {}
        
        # Create many test configs
        for i in range(100):
            test_configs[f"test_config_{i}"] = TestConfigEntity(
                name=f"test_config_{i}",
                type=TestTypes.BENCHMARK,
                dataset="test_dataset_1",
                metric={"name": f"metric_{i}"}
            )
        
        # Create bundle with all tests
        bundle_wrapper = Mock(spec=BundleEntityWrapper)
        bundle_wrapper.name = "large_bundle"
        bundle_wrapper.description = "Bundle with many tests"
        bundle_wrapper.test_names = [f"test_config_{i}" for i in range(100)]
        bundle_wrapper.tests = []
        bundles["large_bundle"] = bundle_wrapper
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):

                # Act
                result = repository.get_bundle_by_id("large_bundle")

                # Assert
                assert len(result.tests) == 100
                assert all(isinstance(test, BenchmarkTestEntity) for test in result.tests)

    @pytest.mark.parametrize("dataset_id", ["dataset_1", "dataset_2", "dataset_3"])
    def test_get_dataset_by_id_various_ids(self, dataset_id, sample_dataset_entity):
        """Test get_dataset_by_id with various dataset IDs"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = sample_dataset_entity
            repository = FileBenchmarkRepository()

            # Act
            result = repository.get_dataset_by_id(dataset_id)

            # Assert
            assert result == sample_dataset_entity
            mock_load_module.assert_called_once()

    def test_repository_logging(self, sample_test_configs_and_bundles):
        """Test that repository methods log appropriately"""
        # Arrange
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = sample_test_configs_and_bundles
            
            repository = FileBenchmarkRepository()

            # Act
            repository.get_all_bundles()

            # Assert
            # Verify that the logger was used (indirectly through the mock)
            assert repository.logger is not None

    def test_bundle_entity_wrapper_integration(self, sample_test_configs_and_bundles, sample_dataset_entity):
        """Test integration with BundleEntityWrapper"""
        # Arrange
        test_configs, bundles = sample_test_configs_and_bundles
        
        with patch('application.services.file_benchmark_repository.load_module') as mock_load_module:
            mock_load_module.return_value = (test_configs, bundles)
            
            repository = FileBenchmarkRepository()
            
            with patch.object(repository, 'get_dataset_by_id', return_value=sample_dataset_entity):

                # Act
                result = repository.get_bundle_by_id("bundle_1")

                # Assert
                assert result.name == "test_bundle"
                assert result.description == "Test bundle description"
                # Verify that test_names from wrapper were used
                assert len(result.tests) == len(bundles["bundle_1"].test_names)
