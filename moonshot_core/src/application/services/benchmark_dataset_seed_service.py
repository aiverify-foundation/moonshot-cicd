"""
Service that seeds the benchmark DB from a dataset loaded by dataset_id.

Loads a dataset via a source DatasetRepository (e.g. FileDatasetRepository)
and persists it using a target DatasetRepository (e.g. SqlAlchemyDatasetRepository
from dataset_adapter.py).
"""

from domain.services.logger import get_logger

from application.ports.dataset_repository import DatasetRepository


class BenchmarkDatasetSeedService:
    """
    Seeds benchmark_test_dataset and benchmark_test_dataset_prompt from a
    dataset loaded by dataset_id.

    Uses a source repository to load (e.g. file by id like "test_sample_dataset")
    and a target repository to save (e.g. SqlAlchemyDatasetRepository from
    dataset_adapter.py for DB persistence).
    """

    def __init__(
        self,
        source_dataset_repository: DatasetRepository,
        target_dataset_repository: DatasetRepository,
    ):
        self.source = source_dataset_repository
        self.target = target_dataset_repository
        self.logger = get_logger(__name__)

    def seed_benchmark_dataset(self, dataset_id: str) -> None:
        """
        Load a dataset by dataset_id from the source repository and insert it
        into the target repository (e.g. DB via dataset_adapter).
        The target assigns version when persisting (e.g. max existing + 1).

        Args:
            dataset_id: Identifier to load from source (e.g. file name without
                extension for FileDatasetRepository, or numeric id for DB).

        Raises:
            ValueError: If source does not have the dataset or target rejects the save.
            NotImplementedError: If target does not support save_dataset.
        """
        self.logger.info("Seeding benchmark dataset: dataset_id=%r", dataset_id)
        entity = self.source.get_dataset_by_id(dataset_id)
        self.target.save_dataset(entity)
        self.logger.info(
            "Seeded benchmark dataset: name=%r, prompts=%s",
            entity.name,
            entity.num_of_dataset_prompts,
        )
