"""Unit tests for BenchmarkDatasetSeedService."""

import pytest
from unittest.mock import Mock

from application.services.benchmark_dataset_seed_service import BenchmarkDatasetSeedService
from domain.entities.dataset_entity import DatasetEntity


class TestBenchmarkDatasetSeedService:
    """Tests for BenchmarkDatasetSeedService."""

    @pytest.fixture
    def source_repo(self):
        return Mock()

    @pytest.fixture
    def target_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, source_repo, target_repo):
        return BenchmarkDatasetSeedService(source_repo, target_repo)

    @pytest.fixture
    def sample_entity(self):
        return DatasetEntity(
            id="file_1",
            name="test_sample_dataset",
            description="Sample for benchmark",
            examples=[
                {"input": "Hello", "target": "Hi"},
                {"input": "Bye", "target": "Goodbye"},
            ],
            num_of_dataset_prompts=2,
            created_date="",
            reference="",
            license="",
        )

    def test_seed_benchmark_dataset_calls_source_and_target(
        self, service, source_repo, target_repo, sample_entity
    ):
        source_repo.get_dataset_by_id.return_value = sample_entity

        service.seed_benchmark_dataset("test_sample_dataset", version=1)

        source_repo.get_dataset_by_id.assert_called_once_with("test_sample_dataset")
        target_repo.save_dataset.assert_called_once_with(
            sample_entity, version=1
        )

    def test_seed_benchmark_dataset_propagates_value_error_from_source(
        self, service, source_repo, target_repo
    ):
        source_repo.get_dataset_by_id.side_effect = ValueError("Dataset not found")

        with pytest.raises(ValueError, match="Dataset not found"):
            service.seed_benchmark_dataset("missing_id")

        target_repo.save_dataset.assert_not_called()

    def test_seed_benchmark_dataset_propagates_value_error_from_target(
        self, service, source_repo, target_repo, sample_entity
    ):
        source_repo.get_dataset_by_id.return_value = sample_entity
        target_repo.save_dataset.side_effect = ValueError(
            "Dataset already exists: system_name='x', version=1"
        )

        with pytest.raises(ValueError, match="Dataset already exists"):
            service.seed_benchmark_dataset("test_sample_dataset", version=1)

    def test_seed_benchmark_dataset_propagates_not_implemented_error_from_target(
        self, service, source_repo, target_repo, sample_entity
    ):
        source_repo.get_dataset_by_id.return_value = sample_entity
        target_repo.save_dataset.side_effect = NotImplementedError("Read-only repository")

        with pytest.raises(NotImplementedError, match="Read-only"):
            service.seed_benchmark_dataset("test_sample_dataset")

    def test_initialization_stores_source_and_target(self, source_repo, target_repo):
        service = BenchmarkDatasetSeedService(source_repo, target_repo)
        assert service.source is source_repo
        assert service.target is target_repo
