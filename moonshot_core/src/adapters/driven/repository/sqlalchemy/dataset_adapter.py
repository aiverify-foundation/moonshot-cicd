"""SQLAlchemy-based implementation of DatasetRepository."""

from typing import Iterator, Optional, override

from application.ports.dataset_repository import DatasetRepository
from domain.entities.dataset_entity import DatasetEntity
from domain.services.logger import configure_logger
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestDatasetModel,
    BenchmarkTestDatasetPromptModel,
)


class SqlAlchemyDatasetRepository(DatasetRepository):
    """
    SQLAlchemy-based implementation of DatasetRepository.

    Reads and writes benchmark datasets via benchmark_test_dataset and
    benchmark_test_dataset_prompt tables. Uses SessionManager for DB access.
    """

    def __init__(self, dataset_source: Optional[object] = None):
        super().__init__(dataset_source)
        self.session_manager = SessionManager.get_instance()
        self.logger = configure_logger(__name__)

    def _parse_dataset_id(self, dataset_id: str) -> int:
        """Parse and validate dataset_id; raise ValueError if invalid."""
        if not dataset_id or not dataset_id.isdigit():
            raise ValueError(f"Invalid dataset_id: {dataset_id!r}")
        return int(dataset_id)

    def _example_pairs(self, examples: Optional[list]) -> Iterator[tuple[str, str]]:
        """Yield (input, target) from each example dict; empty if examples is None."""
        for ex in examples or []:
            yield (ex.get("input") or "", ex.get("target") or "")

    def _model_to_entity(self, model: BenchmarkTestDatasetModel) -> DatasetEntity:
        """Map BenchmarkTestDatasetModel and its prompts to DatasetEntity."""
        examples = [{"input": p.prompt, "target": p.target} for p in model.prompts]
        return DatasetEntity(
            id=str(model.id),
            name=model.system_name,
            description=model.description or "",
            examples=examples,
            num_of_dataset_prompts=len(examples),
            created_date="",
            reference=model.reference or "",
            license=model.license or "",
        )

    def _find_by_name_version(
        self, session, name: str, version: int
    ) -> Optional[BenchmarkTestDatasetModel]:
        """Return existing dataset row if present."""
        return (
            session.query(BenchmarkTestDatasetModel)
            .filter(
                BenchmarkTestDatasetModel.system_name == name,
                BenchmarkTestDatasetModel.version == version,
            )
            .first()
        )

    def _persist_prompts(
        self, session, dataset_id: int, examples: Optional[list]
    ) -> int:
        """Insert prompt rows for dataset_id; return count."""
        pairs = list(self._example_pairs(examples))
        for prompt, target in pairs:
            session.add(
                BenchmarkTestDatasetPromptModel(
                    benchmark_test_dataset_id=dataset_id,
                    prompt=prompt,
                    target=target,
                )
            )
        return len(pairs)

    @override
    def get_dataset_by_id(self, dataset_id: str) -> DatasetEntity:
        """
        Retrieve a dataset by its identifier (DB primary key as string).

        Args:
            dataset_id: The dataset primary key as string (e.g. "1").

        Returns:
            DatasetEntity: The requested dataset entity.

        Raises:
            ValueError: If dataset_id is not a valid integer or dataset not found.
        """
        db_id = self._parse_dataset_id(dataset_id)
        with self.session_manager.get_session() as session:
            model = (
                session.query(BenchmarkTestDatasetModel)
                .filter(BenchmarkTestDatasetModel.id == db_id)
                .first()
            )
        if model is None:
            self.logger.error("Dataset not found: %s", dataset_id)
            raise ValueError(f"Dataset not found: {dataset_id!r}")
        return self._model_to_entity(model)

    @override
    def save_dataset(
        self,
        dataset_entity: DatasetEntity,
        version: int = 1,
    ) -> None:
        """
        Insert a new dataset. Fails if a dataset with the same system_name and
        version already exists.
        """
        entity = dataset_entity
        with self.session_manager.get_session() as session:
            existing = self._find_by_name_version(session, entity.name, version)
            if existing:
                raise ValueError(
                    f"Dataset already exists: system_name={entity.name!r}, version={version}. "
                    "Only insert is allowed; cannot replace."
                )
            new = BenchmarkTestDatasetModel(
                version=version,
                system_name=entity.name,
                description=entity.description or None,
                license=entity.license or None,
                reference=entity.reference or None,
            )
            session.add(new)
            session.flush()
            dataset_id = new.id
            num_prompts = self._persist_prompts(session, dataset_id, entity.examples)
        self.logger.info(
            "Saved dataset: system_name=%r, version=%s, prompts=%s",
            entity.name,
            version,
            num_prompts,
        )
