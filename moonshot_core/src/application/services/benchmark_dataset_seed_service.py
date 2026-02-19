"""
Service that seeds the benchmark DB from a dataset loaded by dataset_id.

Loads a dataset via a source DatasetRepository (e.g. FileDatasetRepository)
and persists it using a target DatasetRepository (e.g. SqlAlchemyDatasetRepository
from dataset_adapter.py).
"""

from application.ports.dataset_repository import DatasetRepository
from domain.services.logger import configure_logger


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
        self.logger = configure_logger(__name__)

    def seed_benchmark_dataset(
        self,
        dataset_id: str,
        version: int = 1,
        replace: bool = False,
    ) -> None:
        """
        Load a dataset by dataset_id from the source repository and persist it
        to the target repository (e.g. DB via dataset_adapter).

        Args:
            dataset_id: Identifier to load from source (e.g. file name without
                extension for FileDatasetRepository, or numeric id for DB).
            version: Dataset version for the target store (e.g. DB version).
            replace: If True, replace existing dataset with same identity in
                target; if False, target may raise when already present.

        Raises:
            ValueError: If source does not have the dataset, or target rejects
                (e.g. already exists and replace=False).
            NotImplementedError: If target does not support save_dataset.
        """
        self.logger.info(f"Seeding benchmark dataset: dataset_id={dataset_id!r}, version={version}, replace={replace}")
        entity = self.source.get_dataset_by_id(dataset_id)
        self.target.save_dataset(entity, version=version, replace=replace)
        self.logger.info(f"Seeded benchmark dataset: name={entity.name!r}, prompts={entity.num_of_dataset_prompts}")
