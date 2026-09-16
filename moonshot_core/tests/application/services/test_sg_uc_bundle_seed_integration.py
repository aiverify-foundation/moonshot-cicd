"""
Integration test: full shared.yaml seed includes the SG UC bundle
(8 Singapore undesirable-content tests / datasets).

Uses an isolated SQLite DB and BenchmarkDatasetSeedService + SharedConfigSeedService
like other application integration tests.
"""

import os
from pathlib import Path

import pytest

from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.dataset_adapter import (
    SqlAlchemyDatasetRepository,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (
    MoonshotConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.benchmark_dataset_seed_service import (
    BenchmarkDatasetSeedService,
)
from application.services.file_dataset_repository import FileDatasetRepository
from application.services.file_shared_config_repository import (
    FileSharedConfigRepository,
)
from application.services.shared_config_seed_service import SharedConfigSeedService

MOONSHOT_CORE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SHARED_CONFIG_PATH = MOONSHOT_CORE_ROOT / "data" / "test_configs" / "shared.yaml"

EXPECTED_SG_UC_DATASETS = sorted(
    [
        "sg_uc_child_sexual_exploitation",
        "sg_uc_hate",
        "sg_uc_nonviolent_crime",
        "sg_uc_selfharm_suicide",
        "sg_uc_sexual_crimes",
        "sg_uc_sexual_content",
        "sg_uc_specialised_advice",
        "sg_uc_violent_content",
    ]
)


@pytest.fixture(scope="session")
def sg_uc_test_db_path():
    db_path = (
        MOONSHOT_CORE_ROOT / "data" / "database" / "moonshot_pytest_sg_uc_bundle.db"
    )
    if db_path.exists():
        db_path.unlink()
    return str(db_path)


@pytest.fixture(scope="session")
def sg_uc_test_db_env(sg_uc_test_db_path):
    old_val = os.environ.get("MOONSHOT_DB_PATH")
    os.environ["MOONSHOT_DB_PATH"] = sg_uc_test_db_path
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    if old_val is not None:
        os.environ["MOONSHOT_DB_PATH"] = old_val
    else:
        os.environ.pop("MOONSHOT_DB_PATH", None)


@pytest.fixture(scope="session")
def sg_uc_shared_config_seed_service(sg_uc_test_db_env):
    shared_config_repo = FileSharedConfigRepository()
    file_dataset_repo = FileDatasetRepository()
    moonshot_config = MoonshotConfigAdapter()
    sqlalchemy_dataset_repo = SqlAlchemyDatasetRepository()
    dataset_seed_service = BenchmarkDatasetSeedService(
        source_dataset_repository=file_dataset_repo,
        target_dataset_repository=sqlalchemy_dataset_repo,
    )
    return SharedConfigSeedService(
        moonshot_config_repository=moonshot_config,
        shared_config_repository=shared_config_repo,
        benchmark_dataset_seed_service=dataset_seed_service,
    )


@pytest.mark.integration
def test_sg_uc_bundle_seeds_eight_tests_with_expected_datasets(
    sg_uc_shared_config_seed_service,
    sg_uc_test_db_env,
):
    assert SHARED_CONFIG_PATH.exists(), f"Missing shared config: {SHARED_CONFIG_PATH}"

    sg_uc_shared_config_seed_service.seed_if_test_file_changed(
        config_path=SHARED_CONFIG_PATH
    )

    config_adapter = BenchmarkTestConfigAdapter()
    bundle_db_id = config_adapter.get_bundle_id_by_system_name_latest("sg-uc")
    test_ids = config_adapter.get_test_ids_by_bundle_id(bundle_db_id)

    assert len(test_ids) == 8, f"Expected 8 tests, got {len(test_ids)}: {test_ids}"

    datasets_in_bundle = sorted(
        {config_adapter.get_test_info(tid)[1] for tid in test_ids}
    )
    assert datasets_in_bundle == EXPECTED_SG_UC_DATASETS

    for tid in test_ids:
        _test_name, _ds, metric_name = config_adapter.get_test_info(tid)
        assert metric_name == "sg_uc_classifier_adapter"

    dataset_repo = SqlAlchemyDatasetRepository()
    for system_name in EXPECTED_SG_UC_DATASETS:
        dataset_id = config_adapter.get_dataset_id_by_system_name_latest(system_name)
        prompts = dataset_repo.get_prompts_by_dataset_id(dataset_id)
        assert (
            len(prompts) >= 1
        ), f"Dataset {system_name!r} should have at least one prompt"
