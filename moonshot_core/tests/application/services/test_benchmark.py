import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from application.services.benchmark import BenchmarkService
from application.dto.bundle_dto import BundleDTO
from application.dto.benchmark_test_dto import BenchmarkTestDTO
from application.dto.dataset_dto import DatasetDTO
from domain.entities.test_bundle_entity import TestBundleEntity
from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.dataset_entity import DatasetEntity


class TestBenchmarkService:
    """Test class for BenchmarkService"""

    @pytest.fixture
    def mock_benchmark_repository(self):
        """Create a mock benchmark repository"""
        return Mock()

    @pytest.fixture
    def mock_dataset_repository(self):
        """Create a mock dataset repository"""
        return Mock()

    @pytest.fixture
    def benchmark_service(self, mock_benchmark_repository, mock_dataset_repository):
        """Create a BenchmarkService instance with mocked dependencies"""
        return BenchmarkService(mock_benchmark_repository, mock_dataset_repository)

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
            name="test_bundle",
            description="Test bundle",
            tests=[sample_benchmark_test_entity],
            category="test_category",
            id="test_bundle"
        )

    def test_initialization_with_repositories(self, mock_benchmark_repository, mock_dataset_repository):
        """Test BenchmarkService initialization with provided repositories"""
        # Act
        service = BenchmarkService(mock_benchmark_repository, mock_dataset_repository)

        # Assert
        assert service.benchmark_repository == mock_benchmark_repository
        assert service.dataset_repository == mock_dataset_repository

    def test_initialization_with_none_repositories(self):
        """Test BenchmarkService initialization with None repositories"""
        # Act
        service = BenchmarkService(None, None)

        # Assert
        assert service.benchmark_repository is not None
        assert service.dataset_repository is not None
        assert isinstance(service.benchmark_repository, type(service.benchmark_repository))
        assert isinstance(service.dataset_repository, type(service.dataset_repository))

    def test_get_bundle_by_id_success(self, benchmark_service, mock_benchmark_repository, mock_dataset_repository, sample_bundle_entity, sample_dataset_entity):
        """Test successful bundle retrieval by ID"""
        # Arrange
        bundle_id = "test_bundle_1"
        mock_benchmark_repository.get_bundle_by_id.return_value = sample_bundle_entity
        mock_dataset_repository.get_dataset_by_id.return_value = sample_dataset_entity

        # Act
        result = benchmark_service.get_bundle_by_id(bundle_id)

        # Assert
        mock_benchmark_repository.get_bundle_by_id.assert_called_once_with(bundle_id)
        assert isinstance(result, BundleDTO)
        assert result.id == sample_bundle_entity.id
        assert result.name == sample_bundle_entity.name
        assert result.description == sample_bundle_entity.description
        assert result.category == sample_bundle_entity.category
        assert len(result.tests) == len(sample_bundle_entity.tests)

    def test_get_bundle_by_id_not_found(self, benchmark_service, mock_benchmark_repository):
        """Test bundle retrieval when bundle is not found"""
        # Arrange
        bundle_id = "nonexistent_bundle"
        mock_benchmark_repository.get_bundle_by_id.side_effect = KeyError("Bundle not found")

        # Act & Assert
        with pytest.raises(KeyError):
            benchmark_service.get_bundle_by_id(bundle_id)

    def test_get_dataset_by_id_success(self, benchmark_service, mock_dataset_repository, sample_dataset_entity):
        """Test successful dataset retrieval by ID"""
        # Arrange
        dataset_id = "test_dataset_1"
        mock_dataset_repository.get_dataset_by_id.return_value = sample_dataset_entity

        # Act
        result = benchmark_service.get_dataset_by_id(dataset_id)

        # Assert
        mock_dataset_repository.get_dataset_by_id.assert_called_once_with(dataset_id)
        assert isinstance(result, DatasetDTO)
        assert result.id == sample_dataset_entity.id
        assert result.name == sample_dataset_entity.name
        assert result.description == sample_dataset_entity.description
        assert result.num_of_dataset_prompts == sample_dataset_entity.num_of_dataset_prompts

    def test_get_dataset_by_id_not_found(self, benchmark_service, mock_dataset_repository):
        """Test dataset retrieval when dataset is not found"""
        # Arrange
        dataset_id = "nonexistent_dataset"
        mock_dataset_repository.get_dataset_by_id.side_effect = Exception("Dataset not found")

        # Act & Assert
        with pytest.raises(Exception):
            benchmark_service.get_dataset_by_id(dataset_id)

    def test_get_benchmark_test_by_id_success(self, benchmark_service, mock_benchmark_repository, mock_dataset_repository, sample_benchmark_test_entity, sample_dataset_entity):
        """Test successful test config retrieval by ID"""
        # Arrange
        test_config_id = "test_config_1"
        mock_benchmark_repository.get_benchmark_test_by_id.return_value = sample_benchmark_test_entity
        mock_dataset_repository.get_dataset_by_id.return_value = sample_dataset_entity

        # Act
        result = benchmark_service.get_benchmark_test_by_id(test_config_id)

        # Assert
        mock_benchmark_repository.get_benchmark_test_by_id.assert_called_once_with(test_config_id)
        assert isinstance(result, BenchmarkTestDTO)
        assert result.id == sample_benchmark_test_entity.id
        assert result.name == sample_benchmark_test_entity.name
        assert result.metric == sample_benchmark_test_entity.metric
        assert result.description == sample_benchmark_test_entity.description
        assert result.requires_llm_aaj is False
        assert result.metric_provider_system_name is None

    def test_get_benchmark_test_by_id_llamaguard_sets_aaj_fields(
        self, benchmark_service, mock_benchmark_repository, mock_dataset_repository, sample_dataset_entity
    ):
        entity = BenchmarkTestEntity(
            id="lg",
            name="lg",
            dataset=sample_dataset_entity,
            metric={"name": "llamaguardannotator_adapter"},
            description="",
        )
        mock_benchmark_repository.get_benchmark_test_by_id.return_value = entity
        mock_dataset_repository.get_dataset_by_id.return_value = sample_dataset_entity
        dto = benchmark_service.get_benchmark_test_by_id("any")
        assert dto.requires_llm_aaj is True
        assert dto.metric_provider_system_name == "together_adapter"

    def test_get_benchmark_test_by_id_not_found(self, benchmark_service, mock_benchmark_repository):
        """Test test config retrieval when config is not found"""
        # Arrange
        test_config_id = "nonexistent_config"
        mock_benchmark_repository.get_benchmark_test_by_id.side_effect = KeyError("Test config not found")

        # Act & Assert
        with pytest.raises(KeyError):
            benchmark_service.get_benchmark_test_by_id(test_config_id)

    def test_get_all_benchmark_tests_success(self, benchmark_service, mock_benchmark_repository, mock_dataset_repository, sample_benchmark_test_entity, sample_dataset_entity):
        """Test successful retrieval of all test configs"""
        # Arrange
        test_entities = [sample_benchmark_test_entity]
        mock_benchmark_repository.get_all_benchmark_tests.return_value = test_entities
        mock_dataset_repository.get_dataset_by_id.return_value = sample_dataset_entity

        # Act
        result = benchmark_service.get_all_benchmark_tests()

        # Assert
        mock_benchmark_repository.get_all_benchmark_tests.assert_called_once()
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], BenchmarkTestDTO)
        assert result[0].name == sample_benchmark_test_entity.name

    def test_get_all_benchmark_tests_empty(self, benchmark_service, mock_benchmark_repository):
        """Test retrieval of all test configs when none exist"""
        # Arrange
        mock_benchmark_repository.get_all_benchmark_tests.return_value = []

        # Act
        result = benchmark_service.get_all_benchmark_tests()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_total_test_list_prompts_success(self, benchmark_service, mock_dataset_repository):
        """Test calculation of total test list prompts"""
        # Arrange
        dataset_entity_1 = DatasetEntity(
            id="dataset_1",
            name="Dataset 1",
            description="First dataset",
            examples=[]
        )
        dataset_entity_1.num_of_dataset_prompts = 5
        
        dataset_entity_2 = DatasetEntity(
            id="dataset_2",
            name="Dataset 2",
            description="Second dataset",
            examples=[]
        )
        dataset_entity_2.num_of_dataset_prompts = 10
        
        mock_dataset_repository.get_dataset_by_id.side_effect = lambda x: dataset_entity_1 if x == "dataset_1" else dataset_entity_2
        
        # Create test configs with just dataset IDs
        dataset_dto_1 = DatasetDTO(
            id="dataset_1",
            name="Dataset 1",
            description="First dataset",
            examples=[]
        )
        dataset_dto_2 = DatasetDTO(
            id="dataset_2",
            name="Dataset 2",
            description="Second dataset",
            examples=[]
        )
        
        test_configs = [
            BenchmarkTestDTO(id="test1", name="test1", dataset=dataset_dto_1, metric={}, description=""),
            BenchmarkTestDTO(id="test2", name="test2", dataset=dataset_dto_2, metric={}, description="")
        ]

        # Act
        result = benchmark_service.get_total_test_list_prompts(test_configs)

        # Assert
        assert result == 15  # 5 + 10

    def test_get_total_test_list_prompts_with_none_dataset(self, benchmark_service):
        """Test calculation of total test list prompts with None dataset"""
        # Arrange
        test_configs = [
            BenchmarkTestDTO(id="test1", name="test1", dataset=None, metric={}, description=""),
            BenchmarkTestDTO(id="test2", name="test2", dataset=None, metric={}, description="")
        ]

        # Act
        result = benchmark_service.get_total_test_list_prompts(test_configs)

        # Assert
        assert result == 0

    def test_get_all_bundles_success(self, benchmark_service, mock_benchmark_repository, mock_dataset_repository, sample_bundle_entity, sample_dataset_entity):
        """Test successful retrieval of all bundles"""
        # Arrange
        bundle_entities = [sample_bundle_entity]
        mock_benchmark_repository.get_all_bundles.return_value = bundle_entities
        mock_dataset_repository.get_dataset_by_id.return_value = sample_dataset_entity

        # Act
        result = benchmark_service.get_all_bundles()

        # Assert
        mock_benchmark_repository.get_all_bundles.assert_called_once()
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], BundleDTO)
        assert result[0].id == sample_bundle_entity.id
        assert result[0].name == sample_bundle_entity.name
        assert result[0].category == sample_bundle_entity.category

    def test_get_all_bundles_empty(self, benchmark_service, mock_benchmark_repository):
        """Test retrieval of all bundles when none exist"""
        # Arrange
        mock_benchmark_repository.get_all_bundles.return_value = []

        # Act
        result = benchmark_service.get_all_bundles()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_number_of_tests_in_bundle(self, benchmark_service):
        """Test calculation of total test list recipes"""
        # Arrange
        test_configs = [
            BenchmarkTestDTO(id="test1", name="test1", dataset=None, metric={}, description=""),
            BenchmarkTestDTO(id="test2", name="test2", dataset=None, metric={}, description=""),
            BenchmarkTestDTO(id="test3", name="test3", dataset=None, metric={}, description="")
        ]

        # Act
        result = benchmark_service.get_number_of_tests_in_bundle(test_configs)

        # Assert
        assert result == 3

    def test_get_number_of_tests_in_bundle_empty(self, benchmark_service):
        """Test calculation of total test list recipes with empty list"""
        # Arrange
        test_configs = []

        # Act
        result = benchmark_service.get_number_of_tests_in_bundle(test_configs)

        # Assert
        assert result == 0

    def test_convert_dataset_entity_to_dto(self, benchmark_service, sample_dataset_entity):
        """Test conversion of DatasetEntity to DatasetDTO"""
        # Act
        result = benchmark_service._convert_dataset_entity_to_dto(sample_dataset_entity)

        # Assert
        assert isinstance(result, DatasetDTO)
        assert result.id == sample_dataset_entity.id
        assert result.name == sample_dataset_entity.name
        assert result.description == sample_dataset_entity.description
        assert result.examples == sample_dataset_entity.examples
        assert result.num_of_dataset_prompts == sample_dataset_entity.num_of_dataset_prompts

    def test_convert_dataset_entity_to_dto_with_iterable_examples(self, benchmark_service):
        """Test conversion of DatasetEntity to DatasetDTO with iterable examples"""
        # Arrange
        dataset_entity = DatasetEntity(
            id="test_id",
            name="Test Name",
            description="Test Description",
            examples=iter([{"input": "test", "output": "result"}])
        )

        # Act
        result = benchmark_service._convert_dataset_entity_to_dto(dataset_entity)

        # Assert
        assert isinstance(result.examples, list)
        assert len(result.examples) == 1

    def test_convert_benchmark_test_entity_to_dto_with_dataset(self, benchmark_service, sample_benchmark_test_entity):
        """Test conversion of BenchmarkTestEntity to BenchmarkTestDTO with dataset"""
        # Act
        result = benchmark_service._convert_benchmark_test_entity_to_dto(sample_benchmark_test_entity)

        # Assert
        assert isinstance(result, BenchmarkTestDTO)
        assert result.id == sample_benchmark_test_entity.id
        assert result.name == sample_benchmark_test_entity.name
        assert result.metric == sample_benchmark_test_entity.metric
        assert result.description == sample_benchmark_test_entity.description
        assert result.dataset is not None
        assert isinstance(result.dataset, DatasetDTO)

    def test_convert_benchmark_test_entity_to_dto_without_dataset(self, benchmark_service):
        """Test conversion of BenchmarkTestEntity to BenchmarkTestDTO without dataset"""
        # Arrange
        benchmark_test_entity = BenchmarkTestEntity(
            id="test_benchmark",
            name="test_benchmark",
            dataset=None,
            metric={"name": "accuracy", "threshold": 0.8},
            description="Test benchmark"
        )

        # Act
        result = benchmark_service._convert_benchmark_test_entity_to_dto(benchmark_test_entity)

        # Assert
        assert isinstance(result, BenchmarkTestDTO)
        assert result.id == benchmark_test_entity.id
        assert result.name == benchmark_test_entity.name
        assert result.metric == benchmark_test_entity.metric
        assert result.description == benchmark_test_entity.description
        assert result.dataset is None

    def test_convert_bundle_entity_to_dto(self, benchmark_service, mock_dataset_repository, sample_bundle_entity, sample_dataset_entity):
        """Test conversion of TestBundleEntity to BundleDTO"""
        # Arrange
        mock_dataset_repository.get_dataset_by_id.return_value = sample_dataset_entity
        
        # Act
        result = benchmark_service._convert_bundle_entity_to_dto(sample_bundle_entity)

        # Assert
        assert isinstance(result, BundleDTO)
        assert result.id == sample_bundle_entity.id
        assert result.name == sample_bundle_entity.name
        assert result.description == sample_bundle_entity.description
        assert result.category == sample_bundle_entity.category
        assert len(result.tests) == len(sample_bundle_entity.tests)
        assert isinstance(result.tests[0], BenchmarkTestDTO)

    def test_convert_bundle_entity_to_dto_empty_tests(self, benchmark_service):
        """Test conversion of TestBundleEntity to BundleDTO with empty tests"""
        # Arrange
        bundle_entity = TestBundleEntity(
            name="empty_bundle",
            description="Empty bundle",
            tests=[],
            category="test_category",
            id="empty_bundle"
        )

        # Act
        result = benchmark_service._convert_bundle_entity_to_dto(bundle_entity)

        # Assert
        assert isinstance(result, BundleDTO)
        assert result.id == bundle_entity.id
        assert result.name == bundle_entity.name
        assert result.description == bundle_entity.description
        assert result.category == bundle_entity.category
        assert len(result.tests) == 0

    def test_repository_exception_handling(self, mock_benchmark_repository, mock_dataset_repository):
        """Test exception handling in repository calls"""
        # Arrange
        mock_benchmark_repository.get_bundle_by_id.side_effect = Exception("Repository error")
        service = BenchmarkService(mock_benchmark_repository, mock_dataset_repository)

        # Act & Assert
        with pytest.raises(Exception):
            service.get_bundle_by_id("test_id")

    def test_multiple_test_configs_conversion(self, benchmark_service, mock_benchmark_repository):
        """Test conversion of multiple test configs"""
        # Arrange
        dataset_entity = DatasetEntity(
            id="dataset_1",
            name="Dataset 1",
            description="Test dataset",
            examples=[{"input": "test", "output": "result"}],
            num_of_dataset_prompts=5
        )
        
        test_entities = [
            BenchmarkTestEntity(
                id="test1",
                name="test1",
                dataset=dataset_entity,
                metric={"name": "accuracy"},
                description="Test 1"
            ),
            BenchmarkTestEntity(
                id="test2",
                name="test2",
                dataset=dataset_entity,
                metric={"name": "precision"},
                description="Test 2"
            )
        ]
        mock_benchmark_repository.get_all_benchmark_tests.return_value = test_entities

        # Act
        result = benchmark_service.get_all_benchmark_tests()

        # Assert
        assert len(result) == 2
        assert result[0].name == "test1"
        assert result[1].name == "test2"
        assert result[0].dataset.num_of_dataset_prompts == 5
        assert result[1].dataset.num_of_dataset_prompts == 5

    def test_edge_case_empty_strings(self, benchmark_service):
        """Test edge cases with empty strings"""
        # Arrange
        dataset_entity = DatasetEntity(
            id="",
            name="",
            description="",
            examples=[],
            num_of_dataset_prompts=0,
            created_date="",
            reference="",
            license=""
        )

        # Act
        result = benchmark_service._convert_dataset_entity_to_dto(dataset_entity)

        # Assert
        assert result.id == ""
        assert result.name == ""
        assert result.description == ""
        assert result.examples == []
        assert result.num_of_dataset_prompts == 0

    def test_large_dataset_conversion(self, benchmark_service):
        """Test conversion of large dataset"""
        # Arrange
        large_examples = [{"example": i} for i in range(1000)]
        dataset_entity = DatasetEntity(
            id="large_dataset",
            name="Large Dataset",
            description="Large dataset for testing",
            examples=large_examples,
            num_of_dataset_prompts=1000
        )

        # Act
        result = benchmark_service._convert_dataset_entity_to_dto(dataset_entity)

        # Assert
        assert len(result.examples) == 1000
        assert result.num_of_dataset_prompts == 1000

    def test_complex_metric_conversion(self, benchmark_service):
        """Test conversion with complex metric structure"""
        # Arrange
        complex_metric = {
            "name": "complex_metric",
            "threshold": 0.85,
            "weights": {"precision": 0.6, "recall": 0.4},
            "categories": ["category1", "category2"],
            "nested": {"config": {"value": 42}}
        }
        
        benchmark_test_entity = BenchmarkTestEntity(
            id="complex_test",
            name="complex_test",
            dataset=None,
            metric=complex_metric,
            description="Complex test"
        )

        # Act
        result = benchmark_service._convert_benchmark_test_entity_to_dto(benchmark_test_entity)

        # Assert
        assert result.metric == complex_metric
        assert result.metric["nested"]["config"]["value"] == 42

    @pytest.mark.parametrize("num_prompts", [0, 1, 100, 1000, 999999])
    def test_various_prompt_counts(self, benchmark_service, mock_dataset_repository, num_prompts):
        """Test various prompt count scenarios"""
        # Arrange
        dataset_entity = DatasetEntity(
            id="test_dataset",
            name="Test Dataset",
            description="Test dataset",
            examples=[]
        )
        dataset_entity.num_of_dataset_prompts = num_prompts
        
        mock_dataset_repository.get_dataset_by_id.return_value = dataset_entity
        
        dataset_dto = DatasetDTO(
            id="test_dataset",
            name="Test Dataset",
            description="Test dataset",
            examples=[]
        )
        
        test_configs = [BenchmarkTestDTO(id="test", name="test", dataset=dataset_dto, metric={}, description="")]

        # Act
        result = benchmark_service.get_total_test_list_prompts(test_configs)

        # Assert
        assert result == num_prompts

    @pytest.mark.parametrize("num_recipes", [0, 1, 5, 10, 100])
    def test_various_recipe_counts(self, benchmark_service, num_recipes):
        """Test various recipe count scenarios"""
        # Arrange
        test_configs = [
            BenchmarkTestDTO(id=f"test_{i}", name=f"test_{i}", dataset=None, metric={}, description="")
            for i in range(num_recipes)
        ]

        # Act
        result = benchmark_service.get_number_of_tests_in_bundle(test_configs)

        # Assert
        assert result == num_recipes

    def test_get_all_bundles_with_dataset_resolution(self, mock_benchmark_repository, mock_dataset_repository):
        """Test that get_all_bundles properly resolves dataset information"""
        # Arrange
        dataset_entity = DatasetEntity(
            id="test_dataset_1",
            name="Test Dataset",
            description="A test dataset",
            examples=[{"input": "test", "output": "result"}],
            num_of_dataset_prompts=10,
            created_date="2023-12-01",
            reference="https://example.com",
            license="MIT"
        )
        
        benchmark_test_entity = BenchmarkTestEntity(
            id="test_benchmark",
            name="test_benchmark",
            dataset=dataset_entity,
            metric={"name": "accuracy", "threshold": 0.8},
            description="Test benchmark"
        )
        
        bundle_entity = TestBundleEntity(
            name="test_bundle",
            description="Test bundle",
            tests=[benchmark_test_entity],
            category="test_category",
            id="test_bundle"
        )
        
        mock_benchmark_repository.get_all_bundles.return_value = [bundle_entity]
        mock_dataset_repository.get_dataset_by_id.return_value = dataset_entity
        
        service = BenchmarkService(mock_benchmark_repository, mock_dataset_repository)

        # Act
        result = service.get_all_bundles()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], BundleDTO)
        assert result[0].name == "test_bundle"
        assert len(result[0].tests) == 1
        
        # Verify dataset information is properly included
        test_dto = result[0].tests[0]
        assert test_dto.dataset is not None
        assert test_dto.dataset.id == "test_dataset_1"
        assert test_dto.dataset.name == "Test Dataset"
        assert test_dto.dataset.description == "A test dataset"
        assert test_dto.dataset.num_of_dataset_prompts == 10

    def test_get_all_bundles_with_null_datasets(self, mock_benchmark_repository, mock_dataset_repository):
        """Test that get_all_bundles handles null datasets properly"""
        # Arrange
        benchmark_test_entity = BenchmarkTestEntity(
            id="test_benchmark",
            name="test_benchmark",
            dataset=None,
            metric={"name": "accuracy", "threshold": 0.8},
            description="Test benchmark"
        )
        
        bundle_entity = TestBundleEntity(
            name="test_bundle",
            description="Test bundle",
            tests=[benchmark_test_entity],
            category="test_category",
            id="test_bundle"
        )
        
        mock_benchmark_repository.get_all_bundles.return_value = [bundle_entity]
        
        service = BenchmarkService(mock_benchmark_repository, mock_dataset_repository)

        # Act
        result = service.get_all_bundles()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        test_dto = result[0].tests[0]
        assert test_dto.dataset is None

    def test_get_all_bundles_multiple_tests_with_datasets(self, mock_benchmark_repository, mock_dataset_repository):
        """Test get_all_bundles with multiple tests having different datasets"""
        # Arrange
        dataset1 = DatasetEntity(
            id="dataset_1",
            name="Dataset 1",
            description="First dataset",
            examples=[],
            num_of_dataset_prompts=5,
            created_date="2023-12-01",
            reference="https://example.com",
            license="MIT"
        )
        
        dataset2 = DatasetEntity(
            id="dataset_2",
            name="Dataset 2",
            description="Second dataset",
            examples=[],
            num_of_dataset_prompts=15,
            created_date="2023-12-02",
            reference="https://example2.com",
            license="Apache"
        )
        
        test1 = BenchmarkTestEntity(
            id="test_1",
            name="test_1",
            dataset=dataset1,
            metric={"name": "accuracy"},
            description="First test"
        )
        
        test2 = BenchmarkTestEntity(
            id="test_2",
            name="test_2",
            dataset=dataset2,
            metric={"name": "refusal"},
            description="Second test"
        )
        
        bundle_entity = TestBundleEntity(
            name="multi_test_bundle",
            description="Bundle with multiple tests",
            tests=[test1, test2],
            category="test_category",
            id="multi_test_bundle"
        )
        
        mock_benchmark_repository.get_all_bundles.return_value = [bundle_entity]
        
        # Mock dataset repository to return datasets by ID
        def mock_get_dataset_by_id(dataset_id):
            if dataset_id == "dataset_1":
                return dataset1
            elif dataset_id == "dataset_2":
                return dataset2
            return None
        
        mock_dataset_repository.get_dataset_by_id.side_effect = mock_get_dataset_by_id
        
        service = BenchmarkService(mock_benchmark_repository, mock_dataset_repository)

        # Act
        result = service.get_all_bundles()

        # Assert
        assert len(result) == 1
        bundle_dto = result[0]
        assert len(bundle_dto.tests) == 2
        
        # Verify first test dataset
        assert bundle_dto.tests[0].dataset.id == "dataset_1"
        assert bundle_dto.tests[0].dataset.name == "Dataset 1"
        assert bundle_dto.tests[0].dataset.num_of_dataset_prompts == 5
        
        # Verify second test dataset
        assert bundle_dto.tests[1].dataset.id == "dataset_2"
        assert bundle_dto.tests[1].dataset.name == "Dataset 2"
        assert bundle_dto.tests[1].dataset.num_of_dataset_prompts == 15

    def test_benchmark_service_with_real_repositories(self):
        """Test BenchmarkService with real repository implementations"""
        # Arrange - Use real repository implementations
        from application.services.file_benchmark_repository import FileBenchmarkRepository
        from application.services.file_dataset_repository import FileDatasetRepository
        
        benchmark_repo = FileBenchmarkRepository("shared.yaml")
        dataset_repo = FileDatasetRepository()
        service = BenchmarkService(benchmark_repo, dataset_repo)

        # Act - Test actual business logic
        bundles = service.get_all_bundles()
        benchmark_tests = service.get_all_benchmark_tests()

        # Assert - Verify business logic works
        assert isinstance(bundles, list)
        assert isinstance(benchmark_tests, list)
        
        # Verify DTO conversion works correctly
        if bundles:
            bundle = bundles[0]
            assert isinstance(bundle, BundleDTO)
            assert bundle.id is not None
            assert bundle.name is not None
            assert bundle.description is not None
            assert bundle.category is not None
            assert isinstance(bundle.tests, list)
            
            # Verify test DTOs within bundles
            for test in bundle.tests:
                assert isinstance(test, BenchmarkTestDTO)
                assert test.id is not None
                assert test.name is not None
                assert test.metric is not None
        
        # Verify benchmark test DTOs
        if benchmark_tests:
            test = benchmark_tests[0]
            assert isinstance(test, BenchmarkTestDTO)
            assert test.id is not None
            assert test.name is not None
            assert test.metric is not None

    def test_total_prompts_calculation_with_real_data(self):
        """Test total prompts calculation with real dataset data"""
        # Arrange - Use real repositories
        from application.services.file_benchmark_repository import FileBenchmarkRepository
        from application.services.file_dataset_repository import FileDatasetRepository
        
        benchmark_repo = FileBenchmarkRepository("shared.yaml")
        dataset_repo = FileDatasetRepository()
        service = BenchmarkService(benchmark_repo, dataset_repo)

        # Act - Get real benchmark tests
        benchmark_tests = service.get_all_benchmark_tests()
        
        if benchmark_tests:  # Only test if we have data
            total_prompts = service.get_total_test_list_prompts(benchmark_tests)

            # Assert - Verify calculation logic
            assert isinstance(total_prompts, int)
            assert total_prompts >= 0
            
            # Verify calculation is correct by checking individual datasets
            expected_total = 0
            for test in benchmark_tests:
                if test.dataset and test.dataset.num_of_dataset_prompts:
                    expected_total += test.dataset.num_of_dataset_prompts
            
            assert total_prompts == expected_total

    def test_number_of_tests_calculation_with_real_data(self):
        """Test number of tests calculation with real data"""
        # Arrange - Use real repositories
        from application.services.file_benchmark_repository import FileBenchmarkRepository
        from application.services.file_dataset_repository import FileDatasetRepository
        
        benchmark_repo = FileBenchmarkRepository("shared.yaml")
        dataset_repo = FileDatasetRepository()
        service = BenchmarkService(benchmark_repo, dataset_repo)

        # Act - Get real benchmark tests
        benchmark_tests = service.get_all_benchmark_tests()
        num_tests = service.get_number_of_tests_in_bundle(benchmark_tests)

        # Assert - Verify calculation logic
        assert isinstance(num_tests, int)
        assert num_tests >= 0
        assert num_tests == len(benchmark_tests)

    def test_dto_conversion_edge_cases(self):
        """Test DTO conversion with edge cases using real data"""
        # Arrange - Use real repositories
        from application.services.file_benchmark_repository import FileBenchmarkRepository
        from application.services.file_dataset_repository import FileDatasetRepository
        
        benchmark_repo = FileBenchmarkRepository("shared.yaml")
        dataset_repo = FileDatasetRepository()
        service = BenchmarkService(benchmark_repo, dataset_repo)

        # Act - Get real data
        bundles = service.get_all_bundles()
        benchmark_tests = service.get_all_benchmark_tests()

        # Assert - Test edge cases in DTO conversion
        if bundles:
            bundle = bundles[0]
            # Test with empty tests
            empty_tests = service.get_number_of_tests_in_bundle([])
            assert empty_tests == 0
            
            # Test with None dataset handling
            total_prompts_empty = service.get_total_test_list_prompts([])
            assert total_prompts_empty == 0
            
            # Test complex metric structures are preserved
            if bundle.tests:
                test = bundle.tests[0]
                assert isinstance(test.metric, dict)
                # Metrics should be preserved as-is from the entity

    def test_undesirable_content_bundle_has_aggregated_details(self):
        from application.services.file_benchmark_repository import FileBenchmarkRepository
        from application.services.file_dataset_repository import FileDatasetRepository

        service = BenchmarkService(
            FileBenchmarkRepository("shared.yaml"),
            FileDatasetRepository(),
        )
        bundles = service.get_all_bundles()
        uc = next(b for b in bundles if b.id == "undesirable-content")

        assert uc.details is not None
        assert len(uc.details) == 24
        assert "row_id" not in uc.details[0]
        assert set(uc.details[0].keys()) == {
            "category_name",
            "dataset",
            "hazard",
            "input",
            "target",
            "response",
            "evaluator_verdict",
        }

    def test_undesirable_content_vcr_test_has_per_dataset_details(self):
        from application.services.file_benchmark_repository import FileBenchmarkRepository
        from application.services.file_dataset_repository import FileDatasetRepository

        service = BenchmarkService(
            FileBenchmarkRepository("shared.yaml"),
            FileDatasetRepository(),
        )
        bundle = service.get_bundle_by_id("undesirable-content")
        vcr_test = next(
            t
            for t in bundle.tests
            if t.dataset and t.dataset.id == "mlc-ailuminate-vcr"
        )

        assert vcr_test.details is not None
        assert len(vcr_test.details) == 2
        assert all(r["dataset"] == "mlc-ailuminate-vcr" for r in vcr_test.details)

    def test_bundle_without_csv_datasets_has_null_details(self):
        from application.services.file_benchmark_repository import FileBenchmarkRepository
        from application.services.file_dataset_repository import FileDatasetRepository

        service = BenchmarkService(
            FileBenchmarkRepository("shared.yaml"),
            FileDatasetRepository(),
        )
        bundle = service.get_bundle_by_id("test-prompts")

        assert bundle.details is None
        assert bundle.tests[0].details is None

    def test_convert_test_entity_attaches_details_from_loader(self, benchmark_service):
        entity = BenchmarkTestEntity(
            id="vcr",
            name="MLCommons AILuminate - Violent Crimes",
            dataset=DatasetEntity(
                id="1",
                name="mlc-ailuminate-vcr",
                description="",
                examples=[],
                num_of_dataset_prompts=100,
            ),
            metric={"name": "llamaguardannotator_adapter"},
            description="desc",
        )
        dto = benchmark_service._convert_benchmark_test_entity_to_dto(entity)

        assert dto.details is not None
        assert len(dto.details) == 2
        assert dto.details[0]["dataset"] == "mlc-ailuminate-vcr"
