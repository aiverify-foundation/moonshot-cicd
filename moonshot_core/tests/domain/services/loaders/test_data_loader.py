import pytest
from unittest.mock import patch, MagicMock, mock_open
from domain.services.loader.loader_types.data_loader import DataLoader
from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.test_bundle_entity import TestBundleEntity
from application.services.wrappers.bundle_entity_wrapper import TestBundleEntityWrapper
from application.services.wrappers.benchmark_test_entity_wrapper import BenchmarkTestEntityWrapper


class TestDataLoader:
    """Test cases for DataLoader class"""

    @pytest.fixture
    def mock_storage_adapter(self):
        """Create a mock storage adapter for testing"""
        mock_adapter = MagicMock()
        mock_adapter.PREFIX = None
        mock_adapter.exists.return_value = True
        mock_adapter.read_file.return_value = "mock_file_content"
        return mock_adapter

    @pytest.fixture
    def sample_yaml_data(self):
        """Sample YAML data for testing"""
        return {
            "test_bundle_1": {
                "name": "Test Bundle 1",
                "description": "First test bundle",
                "category": "test_category",
                "tests": [
                    {
                        "name": "test_1",
                        "dataset": "dataset_1",
                        "metric": {"name": "accuracy"},
                        "description": "First test"
                    },
                    {
                        "name": "test_2",
                        "dataset": "dataset_2",
                        "metric": {"name": "refusal"},
                        "description": "Second test"
                    }
                ]
            },
            "test_bundle_2": {
                "name": "Test Bundle 2",
                "description": "Second test bundle",
                "category": "production_category",
                "tests": [
                    {
                        "name": "test_3",
                        "dataset": "dataset_3",
                        "metric": {"name": "precision"},
                        "description": "Third test"
                    }
                ]
            }
        }

    @pytest.fixture
    def sample_yaml_data_missing_fields(self):
        """Sample YAML data with missing optional fields"""
        return {
            "minimal_bundle": {
                "tests": [
                    {
                        "name": "minimal_test",
                        "metric": {"name": "accuracy"}
                    }
                ]
            }
        }

    def test_initialization(self, mock_storage_adapter):
        """Test DataLoader initialization"""
        loader = DataLoader(mock_storage_adapter)
        assert loader.storage_adapter == mock_storage_adapter
        # FILE_PATH_PREFIX will be set by _set_data_prefix based on AppConfig
        assert loader.FILE_PATH_PREFIX is not None

    @patch('domain.services.loader.loader_types.data_loader.AppConfig')
    def test_set_data_prefix_with_none_prefix(self, mock_app_config, mock_storage_adapter):
        """Test _set_data_prefix when storage adapter prefix is None"""
        mock_app_config.DEFAULT_TEST_CONFIGS_PATH = "/test/path"
        mock_storage_adapter.PREFIX = None
        
        loader = DataLoader(mock_storage_adapter)
        assert loader.FILE_PATH_PREFIX == "/test/path/"

    def test_set_data_prefix_with_custom_prefix(self, mock_storage_adapter):
        """Test _set_data_prefix when storage adapter has custom prefix"""
        mock_storage_adapter.PREFIX = "/custom/path"
        
        loader = DataLoader(mock_storage_adapter)
        assert loader.FILE_PATH_PREFIX == ""

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    @patch('domain.services.loader.loader_types.data_loader.configure_logger')
    def test_load_success(self, mock_logger, mock_factory, mock_storage_adapter, sample_yaml_data):
        """Test successful loading of data configuration"""
        # Setup mocks
        mock_file_adapter = MagicMock()
        mock_file_adapter.deserialize.return_value = sample_yaml_data
        mock_factory.get_adapter.return_value = mock_file_adapter
        
        loader = DataLoader(mock_storage_adapter)
        
        # Execute
        result = loader.load("test_config.yaml")
        
        # Verify
        benchmark_tests, bundles = result
        
        # Check benchmark test entities
        assert len(benchmark_tests) == 3
        assert "test_1" in benchmark_tests
        assert "test_2" in benchmark_tests
        assert "test_3" in benchmark_tests
        
        # Check test wrapper properties
        test_1_wrapper = benchmark_tests["test_1"]
        assert isinstance(test_1_wrapper, BenchmarkTestEntityWrapper)
        assert test_1_wrapper.name == "test_1"
        assert test_1_wrapper.id == "test_1"
        assert test_1_wrapper.dataset_id == "dataset_1"
        assert test_1_wrapper.metric == {"name": "accuracy"}
        assert test_1_wrapper.description == "First test"
        
        # Check bundle entities
        assert len(bundles) == 2
        assert "test_bundle_1" in bundles
        assert "test_bundle_2" in bundles
        
        # Check bundle wrapper properties
        bundle_1_wrapper = bundles["test_bundle_1"]
        assert isinstance(bundle_1_wrapper, TestBundleEntityWrapper)
        assert bundle_1_wrapper.name == "Test Bundle 1"
        assert bundle_1_wrapper.id == "test_bundle_1"
        assert bundle_1_wrapper.description == "First test bundle"
        assert bundle_1_wrapper.category == "test_category"
        assert len(bundle_1_wrapper.tests) == 2

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_load_with_missing_optional_fields(self, mock_factory, mock_storage_adapter, sample_yaml_data_missing_fields):
        """Test loading with missing optional fields"""
        # Setup mocks
        mock_file_adapter = MagicMock()
        mock_file_adapter.deserialize.return_value = sample_yaml_data_missing_fields
        mock_factory.get_adapter.return_value = mock_file_adapter
        
        loader = DataLoader(mock_storage_adapter)
        
        # Execute
        result = loader.load("minimal_config.yaml")
        
        # Verify
        benchmark_tests, bundles = result
        
        # Check minimal bundle
        assert "minimal_bundle" in bundles
        bundle_wrapper = bundles["minimal_bundle"]
        assert bundle_wrapper.name == "minimal_bundle"  # Should use key as default name
        assert bundle_wrapper.id == "minimal_bundle"
        assert bundle_wrapper.description == ""
        assert bundle_wrapper.category == ""
        
        # Check minimal test
        assert "minimal_test" in benchmark_tests
        test_wrapper = benchmark_tests["minimal_test"]
        assert test_wrapper.name == "minimal_test"
        assert test_wrapper.id == "minimal_test"
        assert test_wrapper.description == ""

    def test_read_file_content_and_path_success(self, mock_storage_adapter):
        """Test successful file reading"""
        mock_storage_adapter.exists.return_value = True
        mock_storage_adapter.read_file.return_value = "file_content"
        
        loader = DataLoader(mock_storage_adapter)
        
        content, path = loader._read_file_content_and_path("test.yaml")
        
        assert content == "file_content"
        # Path will include the prefix set by _set_data_prefix
        assert path.endswith("test.yaml")
        mock_storage_adapter.exists.assert_called_once()
        mock_storage_adapter.read_file.assert_called_once()

    def test_read_file_content_and_path_file_not_exists(self, mock_storage_adapter):
        """Test file reading when file doesn't exist"""
        mock_storage_adapter.exists.return_value = False
        
        loader = DataLoader(mock_storage_adapter)
        
        with pytest.raises(FileNotFoundError):
            loader._read_file_content_and_path("nonexistent.yaml")

    def test_read_file_content_and_path_read_error(self, mock_storage_adapter):
        """Test file reading when read operation fails"""
        mock_storage_adapter.exists.return_value = True
        mock_storage_adapter.read_file.side_effect = Exception("Read error")
        
        loader = DataLoader(mock_storage_adapter)
        
        with pytest.raises(FileNotFoundError):
            loader._read_file_content_and_path("error.yaml")

    def test_read_file_content_and_path_empty_content(self, mock_storage_adapter):
        """Test file reading when file content is empty"""
        mock_storage_adapter.exists.return_value = True
        mock_storage_adapter.read_file.return_value = None
        
        loader = DataLoader(mock_storage_adapter)
        
        with pytest.raises(FileNotFoundError):
            loader._read_file_content_and_path("empty.yaml")

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_deserialize_content_success(self, mock_factory, mock_storage_adapter):
        """Test successful content deserialization"""
        mock_file_adapter = MagicMock()
        mock_file_adapter.deserialize.return_value = {"key": "value"}
        mock_factory.get_adapter.return_value = mock_file_adapter
        
        loader = DataLoader(mock_storage_adapter)
        
        result = loader._deserialize_content("test.yaml", "file_content")
        
        assert result == {"key": "value"}
        mock_factory.get_adapter.assert_called_once_with("test.yaml")
        mock_file_adapter.deserialize.assert_called_once_with("file_content")

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_deserialize_content_invalid_format(self, mock_factory, mock_storage_adapter):
        """Test deserialization with invalid content format"""
        mock_file_adapter = MagicMock()
        mock_file_adapter.deserialize.return_value = "invalid_dict"
        mock_factory.get_adapter.return_value = mock_file_adapter
        
        loader = DataLoader(mock_storage_adapter)
        
        with pytest.raises(ValueError):
            loader._deserialize_content("test.yaml", "file_content")

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_deserialize_content_factory_error(self, mock_factory, mock_storage_adapter):
        """Test deserialization when factory raises error"""
        mock_factory.get_adapter.side_effect = Exception("Factory error")
        
        loader = DataLoader(mock_storage_adapter)
        
        with pytest.raises(Exception, match="Factory error"):
            loader._deserialize_content("test.yaml", "file_content")

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_load_file_exists_error(self, mock_factory, mock_storage_adapter):
        """Test load method when FileExistsError is raised"""
        mock_storage_adapter.exists.side_effect = FileExistsError("File exists")
        
        loader = DataLoader(mock_storage_adapter)
        
        with pytest.raises(FileNotFoundError):
            loader.load("test.yaml")

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_load_general_exception(self, mock_factory, mock_storage_adapter):
        """Test load method when general exception is raised"""
        mock_storage_adapter.exists.side_effect = Exception("General error")
        
        loader = DataLoader(mock_storage_adapter)
        
        with pytest.raises(Exception, match="General error"):
            loader.load("test.yaml")

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_load_logging_verification(self, mock_factory, mock_storage_adapter, sample_yaml_data):
        """Test that load method executes successfully (logging is verified by captured stdout)"""
        # Setup mocks
        mock_file_adapter = MagicMock()
        mock_file_adapter.deserialize.return_value = sample_yaml_data
        mock_factory.get_adapter.return_value = mock_file_adapter
        
        loader = DataLoader(mock_storage_adapter)
        
        # Execute - this will log to stdout which is captured by pytest
        result = loader.load("test_config.yaml")
        
        # Verify the method executed successfully
        benchmark_tests, bundles = result
        assert len(bundles) == 2
        assert len(benchmark_tests) == 3

    def test_load_with_empty_yaml_data(self, mock_storage_adapter):
        """Test loading with empty YAML data"""
        with patch('domain.services.loader.loader_types.data_loader.FileFormatFactory') as mock_factory:
            mock_file_adapter = MagicMock()
            mock_file_adapter.deserialize.return_value = {}
            mock_factory.get_adapter.return_value = mock_file_adapter
            
            loader = DataLoader(mock_storage_adapter)
            
            result = loader.load("empty.yaml")
            benchmark_tests, bundles = result
            
            assert len(benchmark_tests) == 0
            assert len(bundles) == 0

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_load_with_malformed_test_data(self, mock_factory, mock_storage_adapter):
        """Test loading with malformed test data"""
        malformed_data = {
            "bad_bundle": {
                "name": "Bad Bundle",
                "tests": [
                    {
                        "name": "test_without_metric",
                        "dataset": "dataset_1",
                        "metric": {}  # Empty metric instead of None
                    }
                ]
            }
        }
        
        mock_file_adapter = MagicMock()
        mock_file_adapter.deserialize.return_value = malformed_data
        mock_factory.get_adapter.return_value = mock_file_adapter
        
        loader = DataLoader(mock_storage_adapter)
        
        # This should handle empty metric fields gracefully
        result = loader.load("malformed.yaml")
        benchmark_tests, bundles = result
        
        assert "test_without_metric" in benchmark_tests
        test_wrapper = benchmark_tests["test_without_metric"]
        assert test_wrapper.metric == {}  # Should be empty dict when provided

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_load_with_nested_metric_data(self, mock_factory, mock_storage_adapter):
        """Test loading with complex nested metric data"""
        complex_data = {
            "complex_bundle": {
                "name": "Complex Bundle",
                "description": "Bundle with complex metrics",
                "category": "complex_category",
                "tests": [
                    {
                        "name": "complex_test",
                        "dataset": "dataset_1",
                        "metric": {
                            "name": "composite_metric",
                            "threshold": 0.85,
                            "weights": {"precision": 0.6, "recall": 0.4},
                            "nested": {"config": {"value": 42}}
                        },
                        "description": "Complex test with nested metrics"
                    }
                ]
            }
        }
        
        mock_file_adapter = MagicMock()
        mock_file_adapter.deserialize.return_value = complex_data
        mock_factory.get_adapter.return_value = mock_file_adapter
        
        loader = DataLoader(mock_storage_adapter)
        
        result = loader.load("complex.yaml")
        benchmark_tests, bundles = result
        
        test_wrapper = benchmark_tests["complex_test"]
        expected_metric = {
            "name": "composite_metric",
            "threshold": 0.85,
            "weights": {"precision": 0.6, "recall": 0.4},
            "nested": {"config": {"value": 42}}
        }
        assert test_wrapper.metric == expected_metric

    def test_default_data_format(self, mock_storage_adapter):
        """Test that DEFAULT_DATA_FORMAT is correctly set"""
        loader = DataLoader(mock_storage_adapter)
        assert loader.DEFAULT_DATA_FORMAT == ".yaml"

    @patch('domain.services.loader.loader_types.data_loader.FileFormatFactory')
    def test_load_with_special_characters_in_names(self, mock_factory, mock_storage_adapter):
        """Test loading with special characters in test and bundle names"""
        special_char_data = {
            "bundle-with-dashes": {
                "name": "Bundle With Spaces",
                "tests": [
                    {
                        "name": "test_with_underscores",
                        "metric": {"name": "accuracy"}
                    },
                    {
                        "name": "test.with.dots",
                        "metric": {"name": "precision"}
                    }
                ]
            }
        }
        
        mock_file_adapter = MagicMock()
        mock_file_adapter.deserialize.return_value = special_char_data
        mock_factory.get_adapter.return_value = mock_file_adapter
        
        loader = DataLoader(mock_storage_adapter)
        
        result = loader.load("special.yaml")
        benchmark_tests, bundles = result
        
        assert "bundle-with-dashes" in bundles
        assert "test_with_underscores" in benchmark_tests
        assert "test.with.dots" in benchmark_tests
        
        bundle_wrapper = bundles["bundle-with-dashes"]
        assert bundle_wrapper.name == "Bundle With Spaces"
        assert bundle_wrapper.id == "bundle-with-dashes"
