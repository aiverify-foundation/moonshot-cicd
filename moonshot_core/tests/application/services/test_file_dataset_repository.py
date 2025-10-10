import pytest
from unittest.mock import Mock, patch
import sys

from application.services.file_dataset_repository import FileDatasetRepository
from domain.entities.dataset_entity import DatasetEntity


class TestFileDatasetRepository:
    """Test class for FileDatasetRepository"""

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
            description="A test dataset for unit testing",
            examples=[{"input": "test", "output": "result"}],
            num_of_dataset_prompts=10,
            created_date="2023-12-01 10:30:00",
            reference="https://example.com/dataset",
            license="MIT"
        )

    @patch('application.services.file_dataset_repository.AppConfig')
    def test_initialization_with_default_source(self, mock_app_config_class):
        """Test FileDatasetRepository initialization with default source"""
        # Arrange
        mock_app_config_class.DEFAULT_DATASETS_PATH = "/default/datasets"

        # Act
        repository = FileDatasetRepository()

        # Assert
        assert repository.dataset_source == "/default/datasets"
        assert repository.logger is not None

    def test_initialization_with_custom_source(self):
        """Test FileDatasetRepository initialization with custom source"""
        # Arrange
        custom_source = "/custom/datasets"

        # Act
        repository = FileDatasetRepository(custom_source)

        # Assert
        assert repository.dataset_source == custom_source
        assert repository.logger is not None

    @patch('application.services.file_dataset_repository.load_module')
    def test_get_dataset_by_id_success(self, mock_load_module, sample_dataset_entity):
        """Test successful dataset retrieval by ID"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "test_dataset_1"
        mock_load_module.return_value = sample_dataset_entity

        # Act
        result = repository.get_dataset_by_id(dataset_id)

        # Assert
        mock_load_module.assert_called_once()
        assert result == sample_dataset_entity
        assert isinstance(result, DatasetEntity)

    @patch('application.services.file_dataset_repository.load_module')
    def test_get_dataset_by_id_with_valid_args(self, mock_load_module, sample_dataset_entity):
        """Test get_dataset_by_id is called with correct arguments"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "valid_dataset_id"
        mock_load_module.return_value = sample_dataset_entity

        # Act
        repository.get_dataset_by_id(dataset_id)

        # Assert
        call_args = mock_load_module.call_args
        assert call_args is not None
        # Verify the arguments passed to load_module
        args = call_args[0]
        kwargs = call_args[1]
        assert len(args) >= 4  # FileLoader, dataset_id, FileTypes.DATASET, success_msg
        assert args[1] == dataset_id
        assert args[2].value == "dataset"  # FileTypes.DATASET
        assert "DATASET_LOADED_MSG" in args[3]
        assert "ERROR_LOADING_DATASET" in args[4]

    @patch('application.services.file_dataset_repository.load_module')
    def test_get_dataset_by_id_exception_handling(self, mock_load_module):
        """Test exception handling in get_dataset_by_id"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "problematic_dataset"
        mock_load_module.side_effect = Exception("Dataset loading failed")

        # Act & Assert
        with pytest.raises(Exception, match="Dataset loading failed"):
            repository.get_dataset_by_id(dataset_id)

    @patch('application.services.file_dataset_repository.load_module')
    def test_get_dataset_by_id_file_not_found(self, mock_load_module):
        """Test get_dataset_by_id when dataset file is not found"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "nonexistent_dataset"
        mock_load_module.side_effect = FileNotFoundError("Dataset file not found")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            repository.get_dataset_by_id(dataset_id)

    @patch('application.services.file_dataset_repository.load_module')
    def test_get_dataset_by_id_permission_error(self, mock_load_module):
        """Test get_dataset_by_id when there's a permission error"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "protected_dataset"
        mock_load_module.side_effect = PermissionError("Permission denied")

        # Act & Assert
        with pytest.raises(PermissionError):
            repository.get_dataset_by_id(dataset_id)

    @patch('application.services.file_dataset_repository.load_module')
    def test_get_dataset_by_id_with_invalid_data(self, mock_load_module):
        """Test get_dataset_by_id with invalid dataset data"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "invalid_dataset"
        mock_load_module.side_effect = ValueError("Invalid dataset format")

        # Act & Assert
        with pytest.raises(ValueError):
            repository.get_dataset_by_id(dataset_id)

    @patch('application.services.file_dataset_repository.load_module')
    def test_get_dataset_by_id_logging_success(self, mock_load_module, sample_dataset_entity):
        """Test that successful dataset loading is logged"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "test_dataset_1"
        mock_load_module.return_value = sample_dataset_entity

        # Mock the logger to capture log calls
        with patch.object(repository.logger, 'info') as mock_info:
            # Act
            repository.get_dataset_by_id(dataset_id)

            # Assert
            assert mock_info.call_count >= 2  # Loading and success messages
            calls = [call[0][0] for call in mock_info.call_args_list]
            assert any("Loading dataset with ID: test_dataset_1" in str(call) for call in calls)
            assert any("Successfully loaded dataset: Test Dataset" in str(call) for call in calls)

    @patch('application.services.file_dataset_repository.load_module')
    def test_get_dataset_by_id_logging_error(self, mock_load_module):
        """Test that dataset loading errors are logged"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "error_dataset"
        mock_load_module.side_effect = Exception("Load error")

        # Mock the logger to capture log calls
        with patch.object(repository.logger, 'info'), patch.object(repository.logger, 'error') as mock_error:
            # Act & Assert
            with pytest.raises(Exception):
                repository.get_dataset_by_id(dataset_id)

            # Assert error was logged
            mock_error.assert_called_once()
            error_call = mock_error.call_args[0][0]
            assert "Failed to load dataset 'error_dataset': Load error" in error_call

    @patch('application.services.file_dataset_repository.load_module')
    def test_multiple_dataset_retrievals(self, mock_load_module):
        """Test multiple dataset retrievals"""
        # Arrange
        repository = FileDatasetRepository()
        
        dataset1 = DatasetEntity(
            id="dataset_1",
            name="Dataset 1",
            description="First dataset",
            examples=[{"input": "test1", "output": "result1"}],
            num_of_dataset_prompts=5
        )
        
        dataset2 = DatasetEntity(
            id="dataset_2",
            name="Dataset 2",
            description="Second dataset",
            examples=[{"input": "test2", "output": "result2"}],
            num_of_dataset_prompts=10
        )

        mock_load_module.side_effect = [dataset1, dataset2]

        # Act
        result1 = repository.get_dataset_by_id("dataset_1")
        result2 = repository.get_dataset_by_id("dataset_2")

        # Assert
        assert result1 == dataset1
        assert result2 == dataset2
        assert mock_load_module.call_count == 2

    def test_empty_dataset_id(self):
        """Test get_dataset_by_id with empty dataset ID"""
        # Arrange
        repository = FileDatasetRepository()

        # Act & Assert
        with pytest.raises(Exception):
            # This should fail as load_module will likely raise an exception
            repository.get_dataset_by_id("")

    def test_none_dataset_id(self):
        """Test get_dataset_by_id with None dataset ID"""
        # Arrange
        repository = FileDatasetRepository()

        # Act & Assert
        with pytest.raises(Exception):
            # This should fail as load_module expects a string
            repository.get_dataset_by_id(None)

    @patch('application.services.file_dataset_repository.load_module')
    def test_dataset_with_special_characters_in_id(self, mock_load_module, sample_dataset_entity):
        """Test get_dataset_by_id with special characters in dataset ID"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "dataset-with-special_chars.123"
        mock_load_module.return_value = sample_dataset_entity

        # Act
        result = repository.get_dataset_by_id(dataset_id)

        # Assert
        assert result == sample_dataset_entity
        mock_load_module.assert_called_once()

    @patch('application.services.file_dataset_repository.load_module')
    def test_dataset_with_unicode_characters(self, mock_load_module):
        """Test get_dataset_by_id with unicode characters"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_id = "dataset_测试_データセット"
        dataset_entity = DatasetEntity(
            id=dataset_id,
            name="Unicode Dataset",
            description="Dataset with unicode characters",
            examples=[{"input": "测试", "output": "結果"}],
            num_of_dataset_prompts=3
        )
        mock_load_module.return_value = dataset_entity

        # Act
        result = repository.get_dataset_by_id(dataset_id)

        # Assert
        assert result == dataset_entity
        assert result.id == dataset_id

    @patch('application.services.file_dataset_repository.load_module')
    def test_large_dataset_entity(self, mock_load_module):
        """Test get_dataset_by_id with large dataset entity"""
        # Arrange
        repository = FileDatasetRepository()
        large_examples = [{"example": i, "data": f"large_data_{i}"} for i in range(1000)]
        large_dataset = DatasetEntity(
            id="large_dataset",
            name="Large Dataset",
            description="Dataset with many examples",
            examples=large_examples,
            num_of_dataset_prompts=1000,
            created_date="2023-12-01",
            reference="https://example.com/large",
            license="Apache 2.0"
        )
        mock_load_module.return_value = large_dataset

        # Act
        result = repository.get_dataset_by_id("large_dataset")

        # Assert
        assert result == large_dataset
        assert len(result.examples) == 1000
        assert result.num_of_dataset_prompts == 1000

    @patch('application.services.file_dataset_repository.load_module')
    def test_dataset_with_complex_examples(self, mock_load_module):
        """Test get_dataset_by_id with complex example structures"""
        # Arrange
        repository = FileDatasetRepository()
        complex_examples = [
            {
                "input": {
                    "prompt": "Complex prompt",
                    "context": ["context1", "context2"],
                    "metadata": {"source": "test", "priority": "high"}
                },
                "output": {
                    "response": "Complex response",
                    "confidence": 0.95,
                    "details": {"category": "test", "score": 85}
                }
            }
        ]
        complex_dataset = DatasetEntity(
            id="complex_dataset",
            name="Complex Dataset",
            description="Dataset with complex examples",
            examples=complex_examples,
            num_of_dataset_prompts=1
        )
        mock_load_module.return_value = complex_dataset

        # Act
        result = repository.get_dataset_by_id("complex_dataset")

        # Assert
        assert result == complex_dataset
        assert len(result.examples) == 1
        assert result.examples[0]["input"]["metadata"]["source"] == "test"

    @patch('application.services.file_dataset_repository.load_module')
    def test_concurrent_dataset_access(self, mock_load_module):
        """Test concurrent access to different datasets"""
        # Arrange
        repository = FileDatasetRepository()
        
        dataset1 = DatasetEntity(
            id="concurrent_dataset_1",
            name="Concurrent Dataset 1",
            description="First concurrent dataset",
            examples=[],
            num_of_dataset_prompts=5
        )
        
        dataset2 = DatasetEntity(
            id="concurrent_dataset_2",
            name="Concurrent Dataset 2",
            description="Second concurrent dataset",
            examples=[],
            num_of_dataset_prompts=7
        )

        mock_load_module.side_effect = [dataset1, dataset2]

        # Act - simulate concurrent access
        result1 = repository.get_dataset_by_id("concurrent_dataset_1")
        result2 = repository.get_dataset_by_id("concurrent_dataset_2")

        # Assert
        assert result1 == dataset1
        assert result2 == dataset2
        
    @pytest.mark.parametrize("dataset_id", [
        "simple_dataset",
        "dataset_with_numbers123",
        "dataset-with-hyphens",
        "dataset.with.dots",
        "dataset_with_underscores",
        "UPPERCASE_DATASET",
        "MixedCase_Dataset",
        "dataset with spaces",
        "dataset!@#special_chars"
    ])
    @patch('application.services.file_dataset_repository.load_module')
    def test_various_dataset_id_formats(self, mock_load_module, dataset_id):
        """Test get_dataset_by_id with various dataset ID formats"""
        # Arrange
        repository = FileDatasetRepository()
        dataset_entity = DatasetEntity(
            id=dataset_id,
            name=f"Dataset {dataset_id}",
            description=f"Description for {dataset_id}",
            examples=[],
            num_of_dataset_prompts=1
        )
        mock_load_module.return_value = dataset_entity

        # Act
        result = repository.get_dataset_by_id(dataset_id)

        # Assert
        assert result == dataset_entity
        mock_load_module.assert_called_once()

    @patch('application.services.file_dataset_repository.load_module')
    def test_repository_inheritance_from_DatasetRepository(self, mock_load_module, sample_dataset_entity):
        """Test that FileDatasetRepository implements DatasetRepository interface"""
        # Arrange
        repository = FileDatasetRepository()
        mock_load_module.return_value = sample_dataset_entity

        # Act
        result = repository.get_dataset_by_id("test_id")

        # Assert
        assert isinstance(repository, type(repository).__bases__[0])  # Check inheritance
        assert result == sample_dataset_entity

    @patch('application.services.file_dataset_repository.load_module')
    def test_logger_initialization(self, mock_load_module):
        """Test that logger is properly initialized"""
        # Arrange
        repository = FileDatasetRepository()

        # Assert
        assert repository.logger is not None
        assert hasattr(repository.logger, 'info')
        assert hasattr(repository.logger, 'error')

    def test_repository_initialization_with_custom_app_config(self):
        """Test repository initialization with custom AppConfig setup"""
        # Arrange
        custom_source = "/custom/path/to/datasets"
        
        # Act
        repository = FileDatasetRepository(custom_source)

        # Assert
        assert repository.dataset_source == custom_source
        assert repository.logger is not None

    @patch('application.services.file_dataset_repository.load_module')
    def test_dataset_with_minimal_required_fields(self, mock_load_module):
        """Test dataset retrieval with minimal required fields"""
        # Arrange
        repository = FileDatasetRepository()
        minimal_dataset = DatasetEntity(
            id="minimal_dataset",
            name="Minimal Dataset",
            description="A minimal dataset",
            examples=[]
        )
        mock_load_module.return_value = minimal_dataset

        # Act
        result = repository.get_dataset_by_id("minimal_dataset")

        # Assert
        assert result == minimal_dataset
        assert result.num_of_dataset_prompts == 0  # Default value
        assert result.created_date == ""  # Default value
        assert result.reference == ""  # Default value
        assert result.license == ""  # Default value

    @patch('application.services.file_dataset_repository.load_module')
    def test_dataset_with_maximal_fields(self, mock_load_module):
        """Test dataset retrieval with all fields populated"""
        # Arrange
        repository = FileDatasetRepository()
        maximal_dataset = DatasetEntity(
            id="maximal_dataset",
            name="Maximal Dataset",
            description="A dataset with all fields populated",
            examples=[{"input": "test", "output": "result"}] * 100,
            num_of_dataset_prompts=100,
            created_date="2023-12-01 00:00:00",
            reference="https://example.com/maximal",
            license="GPL v3"
        )
        mock_load_module.return_value = maximal_dataset

        # Act
        result = repository.get_dataset_by_id("maximal_dataset")

        # Assert
        assert result == maximal_dataset
        assert len(result.examples) == 100
        assert result.num_of_dataset_prompts == 100
        assert result.created_date == "2023-12-01 00:00:00"
        assert result.reference == "https://example.com/maximal"
        assert result.license == "GPL v3"

    def test_get_dataset_by_id_with_real_dataset_file(self):
        """Test get_dataset_by_id with actual dataset file"""
        # Arrange - Use a real dataset file
        repository = FileDatasetRepository()
        
        # Act - Try to load a dataset that should exist
        result = repository.get_dataset_by_id("brand_reputation_bbq")
        
        # Assert
        assert isinstance(result, DatasetEntity)
        assert result.id == "brand_reputation_bbq"
        assert result.name is not None
        assert result.description is not None
        assert isinstance(result.examples, list)
        assert result.num_of_dataset_prompts > 0
        
        # Verify dataset structure
        if result.examples:
            example = result.examples[0]
            assert isinstance(example, dict)
            # Should have input/output structure typical of datasets

    def test_get_dataset_by_id_with_nonexistent_dataset(self):
        """Test get_dataset_by_id with dataset that doesn't exist"""
        # Arrange
        repository = FileDatasetRepository()
        
        # Act & Assert
        with pytest.raises(Exception):  # Should raise an exception for nonexistent dataset
            repository.get_dataset_by_id("nonexistent_dataset_12345")

    def test_dataset_loading_error_handling(self):
        """Test proper error handling when dataset loading fails"""
        # Arrange
        repository = FileDatasetRepository()
        
        # Act & Assert - Try to load with invalid dataset ID
        with pytest.raises(Exception):
            repository.get_dataset_by_id("")  # Empty string should fail
            
        with pytest.raises(Exception):
            repository.get_dataset_by_id(None)  # None should fail
