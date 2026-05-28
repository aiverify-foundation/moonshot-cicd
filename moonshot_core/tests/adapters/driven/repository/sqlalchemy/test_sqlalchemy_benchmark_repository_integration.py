"""Integration tests: SqlAlchemyBenchmarkRepository reads bundles seeded in the DB."""

from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.dataset_adapter import SqlAlchemyDatasetRepository
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import MoonshotConfigAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from adapters.driven.repository.sqlalchemy.sqlalchemy_benchmark_repository import (
    SqlAlchemyBenchmarkRepository,
)
from application.services.shared_config_seed_service import SHARED_CONFIG_SEED_VERSION_KEY
from application.services.benchmark import BenchmarkService
from application.services.benchmark_dataset_seed_service import BenchmarkDatasetSeedService
from application.services.file_dataset_repository import FileDatasetRepository
from application.services.shared_config_seed_service import SharedConfigSeedService


MOONSHOT_CORE_ROOT = Path(__file__).resolve().parents[5]
FIXTURE_CONFIG = (
    MOONSHOT_CORE_ROOT
    / "tests"
    / "application"
    / "services"
    / "fixtures"
    / "shared_minimal.yaml"
)


@pytest.fixture
def listing_db(tmp_path, monkeypatch):
    db_path = tmp_path / "sqlalchemy_benchmark_listing.db"
    monkeypatch.setenv("MOONSHOT_DB_PATH", str(db_path))
    SessionManager.reset_instance()
    yield str(db_path)
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.mark.integration
def test_get_all_bundles_returns_minimal_bundle_from_db(listing_db):
    assert FIXTURE_CONFIG.exists(), f"Missing fixture: {FIXTURE_CONFIG}"

    dataset_seed = BenchmarkDatasetSeedService(
        source_dataset_repository=FileDatasetRepository(),
        target_dataset_repository=SqlAlchemyDatasetRepository(),
    )
    dataset_seed.seed_benchmark_dataset("test_sample_dataset")
    SharedConfigSeedService().seed_from_config(FIXTURE_CONFIG, version=1)

    ds_repo = SqlAlchemyDatasetRepository()
    repo = SqlAlchemyBenchmarkRepository(ds_repo)
    service = BenchmarkService(repo, ds_repo)

    bundles = service.get_all_bundles()
    assert len(bundles) >= 1
    minimal = next(b for b in bundles if b.id == "minimal-bundle")
    assert minimal.name == "Minimal Bundle"
    assert len(minimal.tests) == 1
    t0 = minimal.tests[0]
    assert t0.name == "Sample Test"
    assert isinstance(t0.benchmark_test_id, int) and t0.benchmark_test_id > 0
    assert t0.metric.get("name") == "refusal_adapter"
    assert t0.requires_llm_aaj is True
    assert t0.metric_provider_system_name == "openai_adapter"
    assert t0.dataset is not None
    assert minimal.prompt_count == t0.dataset.num_of_dataset_prompts


@pytest.mark.integration
def test_llamaguard_test_has_aaj_fields_in_dto(listing_db):
    """Seed one test with llamaguardannotator_adapter via in-memory YAML fragment."""
    dataset_seed = BenchmarkDatasetSeedService(
        source_dataset_repository=FileDatasetRepository(),
        target_dataset_repository=SqlAlchemyDatasetRepository(),
    )
    dataset_seed.seed_benchmark_dataset("test_sample_dataset")
    data = {
        "lg-bundle": {
            "name": "LG Bundle",
            "category": "test",
            "tests": [
                {
                    "name": "LG Test",
                    "type": "benchmark",
                    "dataset": "test_sample_dataset",
                    "metric": {"name": "llamaguardannotator_adapter"},
                    "description": "Eval line one.\nEval line two.",
                },
            ],
        }
    }
    SharedConfigSeedService().seed_from_data(data, config_path=None, version=1)

    ds_repo = SqlAlchemyDatasetRepository()
    service = BenchmarkService(SqlAlchemyBenchmarkRepository(ds_repo), ds_repo)
    bundles = service.get_all_bundles()
    lg = next(b for b in bundles if b.id == "lg-bundle")
    assert len(lg.tests) == 1
    dto = lg.tests[0]
    assert dto.metric.get("name") == "llamaguardannotator_adapter"
    assert dto.requires_llm_aaj is True
    assert dto.metric_provider_system_name == "together_adapter"
    assert "Eval line one" in (dto.description or "")


@pytest.mark.integration
def test_get_all_bundles_filters_by_seed_version_and_visible(listing_db):
    """Portal listing includes only bundles at current seed version with visible=true."""
    dataset_seed = BenchmarkDatasetSeedService(
        source_dataset_repository=FileDatasetRepository(),
        target_dataset_repository=SqlAlchemyDatasetRepository(),
    )
    dataset_seed.seed_benchmark_dataset("test_sample_dataset")

    base_test = {
        "type": "benchmark",
        "dataset": "test_sample_dataset",
        "metric": {"name": "refusal_adapter"},
    }
    SharedConfigSeedService().seed_from_data(
        {
            "bundle-a": {
                "name": "A",
                "category": "c",
                "tests": [{**base_test, "name": "Test A"}],
            },
            "bundle-b": {
                "name": "B",
                "category": "c",
                "tests": [{**base_test, "name": "Test B"}],
            },
        },
        version=1,
    )
    MoonshotConfigAdapter().set(SHARED_CONFIG_SEED_VERSION_KEY, "1")

    SharedConfigSeedService().seed_from_data(
        {
            "bundle-a": {
                "name": "A",
                "category": "c",
                "visible": False,
                "tests": [{**base_test, "name": "Test A"}],
            },
            "bundle-c": {
                "name": "C",
                "category": "c",
                "tests": [{**base_test, "name": "Test C"}],
            },
        },
        version=2,
    )
    MoonshotConfigAdapter().set(SHARED_CONFIG_SEED_VERSION_KEY, "2")

    ds_repo = SqlAlchemyDatasetRepository()
    bundles = BenchmarkService(
        SqlAlchemyBenchmarkRepository(ds_repo), ds_repo
    ).get_all_bundles()

    assert {b.id for b in bundles} == {"bundle-c"}
