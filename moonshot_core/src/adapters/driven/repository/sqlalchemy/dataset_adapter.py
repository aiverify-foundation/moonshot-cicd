"""SQLAlchemy-based implementation of DatasetRepository."""

from typing import Optional, override

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from application.ports.dataset_repository import DatasetRepository
from domain.entities.benchmark_test_dataset_prompt_entity import (
    BenchmarkTestDatasetPromptEntity,
)
from domain.entities.dataset_entity import DatasetEntity
from domain.services.dataset_examples_converter import (
    examples_to_prompts,
    prompts_to_examples,
)
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

    def _model_to_entity(self, model: BenchmarkTestDatasetModel) -> DatasetEntity:
        """Map BenchmarkTestDatasetModel and its prompts to DatasetEntity."""
        prompt_entities: list[BenchmarkTestDatasetPromptEntity] = [
            BenchmarkTestDatasetPromptEntity(
                id=p.id,
                benchmark_test_dataset_id=p.benchmark_test_dataset_id,
                prompt=p.prompt,
                target=p.target,
            )
            for p in model.prompts
        ]
        examples = prompts_to_examples(prompt_entities)
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

    def _get_max_version_for_name(self, session, name: str) -> int:
        """Return the latest version for this system_name, or 0 if none."""
        result = (
            session.query(func.max(BenchmarkTestDatasetModel.version))
            .filter(BenchmarkTestDatasetModel.system_name == name)
            .scalar()
        )
        return result if result is not None else 0

    def _persist_prompts(
        self, session, dataset_id: int, examples: Optional[list]
    ) -> int:
        """Insert prompt rows for dataset_id; return count. examples: list of dicts (input/target)."""
        prompts = examples_to_prompts(examples or [])
        for p in prompts:
            session.add(
                BenchmarkTestDatasetPromptModel(
                    benchmark_test_dataset_id=dataset_id,
                    prompt=p.prompt,
                    target=p.target,
                )
            )
        return len(prompts)

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
                .options(joinedload(BenchmarkTestDatasetModel.prompts))
                .filter(BenchmarkTestDatasetModel.id == db_id)
                .first()
            )
            if model is None:
                self.logger.error("Dataset not found: %s", dataset_id)
                raise ValueError(f"Dataset not found: {dataset_id!r}")
            return self._model_to_entity(model)

    @override
    def get_prompts_by_dataset_id(
        self, dataset_id: int
    ) -> list[BenchmarkTestDatasetPromptEntity]:
        """
        Return all dataset prompts for the given benchmark_test_dataset id.
        """
        with self.session_manager.get_session() as session:
            models = (
                session.query(BenchmarkTestDatasetPromptModel)
                .filter(
                    BenchmarkTestDatasetPromptModel.benchmark_test_dataset_id
                    == dataset_id,
                )
                .all()
            )
            return [
                BenchmarkTestDatasetPromptEntity(
                    id=m.id,
                    benchmark_test_dataset_id=m.benchmark_test_dataset_id,
                    prompt=m.prompt,
                    target=m.target,
                )
                for m in models
            ]

    @override
    def save_dataset(self, dataset_entity: DatasetEntity) -> None:
        """
        Insert a new dataset. If a dataset with the same system_name exists,
        use max(version)+1; otherwise use version 1.
        system_name is set from entity.id (config/file key) so YAML dataset keys match lookups.
        """
        entity = dataset_entity
        # Use entity.id (loader name / file key) as system_name so config references find this row
        name_key = entity.id
        with self.session_manager.get_session() as session:
            max_version = self._get_max_version_for_name(session, name_key)
            version = max_version + 1
            new = BenchmarkTestDatasetModel(
                version=version,
                system_name=name_key,
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
            name_key,
            version,
            num_prompts,
        )
