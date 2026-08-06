from domain.entities.benchmark_test_entity import BenchmarkTestEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.test_bundle_entity import TestBundleEntity
from domain.entities.test_config_entity import TestConfigEntity
from domain.services.dataset_examples_converter import prompts_to_examples
from domain.services.metric_aaj_requirements import (
    metric_aaj_fields,
    metric_grader_model_name,
)
from domain.services.logger import configure_logger
from domain.services.app_config import AppConfig
from application.services.file_benchmark_repository import FileBenchmarkRepository
from application.services.file_dataset_repository import FileDatasetRepository
from application.ports.benchmark_repository import BenchmarkRepository
from application.ports.dataset_repository import DatasetRepository
from application.dto.bundle_dto import BundleDTO
from application.dto.benchmark_test_dto import BenchmarkTestDTO
from application.dto.dataset_dto import DatasetDTO
from application.services.test_details_loader import (
    TestDetailsLoader,
    dataset_system_name_for_details,
)

# Initialize a logger for this module
logger = configure_logger(__name__)


class BenchmarkService:
    """
    Service class for managing benchmark operations and data conversion.

    This service acts as an intermediary between the application layer and the repository layer,
    providing business logic for benchmark operations and converting between domain entities
    and data transfer objects (DTOs).

    The service handles operations such as retrieving bundles, datasets, and benchmark tests,
    as well as calculating aggregate metrics like total prompt counts across test configurations.
    """

    def __init__(
        self,
        benchmark_repository: BenchmarkRepository,
        dataset_repository: DatasetRepository,
        test_details_loader: TestDetailsLoader | None = None,
        app_config: AppConfig | None = None,
    ):
        logger.info("[BenchmarkService] Initializing BenchmarkService")
        self.benchmark_repository = benchmark_repository
        self.dataset_repository = dataset_repository
        self._test_details_loader = test_details_loader or TestDetailsLoader()
        self._app_config = app_config or AppConfig()
        if self.benchmark_repository is None:
            self.benchmark_repository = FileBenchmarkRepository()
        if self.dataset_repository is None:
            self.dataset_repository = FileDatasetRepository()

    def get_bundle_by_id(self, bundle_id: str) -> BundleDTO:
        bundle_entity = self.benchmark_repository.get_bundle_by_id(bundle_id)
        return self._convert_bundle_entity_to_dto(bundle_entity)

    def get_dataset_by_id(self, dataset_id: str) -> DatasetDTO:
        dataset_entity = self.dataset_repository.get_dataset_by_id(dataset_id)
        return self._convert_dataset_entity_to_dto(dataset_entity)

    def get_benchmark_test_by_id(self, test_config_id: str) -> BenchmarkTestDTO:
        benchmark_test_entity = self.benchmark_repository.get_benchmark_test_by_id(
            test_config_id
        )
        return self._convert_benchmark_test_entity_to_dto(benchmark_test_entity)

    def get_all_benchmark_tests(self) -> list[BenchmarkTestDTO]:
        benchmark_test_entities = self.benchmark_repository.get_all_benchmark_tests()
        benchmark_test_dtos = []
        for benchmark_test_entity in benchmark_test_entities:
            benchmark_test_dto = self._convert_benchmark_test_entity_to_dto(
                benchmark_test_entity
            )
            benchmark_test_dtos.append(benchmark_test_dto)
        return benchmark_test_dtos

    def get_total_test_list_prompts(self, test_configs: list[BenchmarkTestDTO]) -> int:
        # This is the total number of prompts in the test list
        # Business logic, we only have one dataset per test
        return sum(
            self.get_dataset_by_id(test_config.dataset.id).num_of_dataset_prompts
            for test_config in test_configs
            if test_config.dataset
        )

    def get_all_bundles(self) -> list[BundleDTO]:
        bundle_entities = self.benchmark_repository.get_all_bundles()
        bundle_dtos = []
        for bundle_entity in bundle_entities:
            bundle_dto = self._convert_bundle_entity_to_dto(bundle_entity)
            bundle_dtos.append(bundle_dto)
        return bundle_dtos

    def get_number_of_tests_in_bundle(
        self, test_configs: list[BenchmarkTestDTO]
    ) -> int:
        # Return the number of test configurations (recipes)
        return len(test_configs)

    def _convert_dataset_entity_to_dto(
        self, dataset_entity: DatasetEntity
    ) -> DatasetDTO:
        """Convert DatasetEntity to DatasetDTO. Uses prompts_to_examples if examples are prompt entities."""
        examples = dataset_entity.examples or []
        if examples and hasattr(examples[0], "prompt"):
            examples_for_dto = prompts_to_examples(examples)
        else:
            examples_for_dto = (
                list(examples) if hasattr(examples, "__iter__") else examples
            )
        return DatasetDTO(
            id=dataset_entity.id,
            name=dataset_entity.name,
            description=dataset_entity.description,
            examples=examples_for_dto,
            num_of_dataset_prompts=dataset_entity.num_of_dataset_prompts,
        )

    def _convert_benchmark_test_entity_to_dto(
        self, benchmark_test_entity: BenchmarkTestEntity
    ) -> BenchmarkTestDTO:
        """Convert BenchmarkTestEntity to BenchmarkTestDTO."""
        dataset_dto = None
        if benchmark_test_entity.dataset:
            dataset_dto = self._convert_dataset_entity_to_dto(
                benchmark_test_entity.dataset
            )

        requires_llm_aaj, metric_provider_system_name = metric_aaj_fields(
            benchmark_test_entity.metric
        )
        grader_model = metric_grader_model_name(
            benchmark_test_entity.metric, app_config=self._app_config
        )
        details = None
        if benchmark_test_entity.dataset:
            ds = benchmark_test_entity.dataset
            details = self._test_details_loader.get_rows_for_dataset(
                dataset_system_name_for_details(ds.id, ds.name)
            )
        return BenchmarkTestDTO(
            id=benchmark_test_entity.id,
            name=benchmark_test_entity.name,
            dataset=dataset_dto,
            metric=benchmark_test_entity.metric,
            description=benchmark_test_entity.description,
            requires_llm_aaj=requires_llm_aaj,
            metric_provider_system_name=metric_provider_system_name,
            metric_grader_model_name=grader_model,
            benchmark_test_id=benchmark_test_entity.benchmark_test_id,
            details=details,
        )

    def _convert_bundle_entity_to_dto(
        self, bundle_entity: TestBundleEntity
    ) -> BundleDTO:
        """Convert TestBundleEntity to BundleDTO."""
        test_dtos = []
        for test_entity in bundle_entity.tests:
            test_dto = self._convert_benchmark_test_entity_to_dto(test_entity)
            test_dtos.append(test_dto)

        # Calculate total prompt count across all tests in the bundle
        prompt_count = self.get_total_test_list_prompts(test_dtos)

        dataset_names = [
            dataset_system_name_for_details(t.dataset.id, t.dataset.name)
            for t in test_dtos
            if t.dataset
        ]
        dataset_names = [n for n in dataset_names if n]
        bundle_details = self._test_details_loader.get_rows_for_datasets(dataset_names)

        return BundleDTO(
            id=bundle_entity.id,
            name=bundle_entity.name,
            description=bundle_entity.description,
            category=bundle_entity.category,
            tests=test_dtos,
            prompt_count=prompt_count,
            details=bundle_details,
        )
