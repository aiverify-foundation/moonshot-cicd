"""
Integration test: seed shared config merged with benchmark-extensions overlay.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from domain.services.enums.feature_flag_names import FeatureFlagNames

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkTestBundleModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.benchmark_dataset_seed_service import (
    BenchmarkDatasetSeedService,
)
from application.services.file_dataset_repository import FileDatasetRepository
from application.services.file_shared_config_repository import FileSharedConfigRepository
from application.services.shared_config_seed_service import SharedConfigSeedService
from adapters.driven.repository.sqlalchemy.dataset_adapter import (
    SqlAlchemyDatasetRepository,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (
    MoonshotConfigAdapter,
)


@pytest.fixture
def test_db_path():
    moonshot_core_root = Path(__file__).resolve().parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_extensions.db"
    if db_path.exists():
        db_path.unlink()
    yield str(db_path)


@pytest.fixture
def test_db_env(test_db_path, monkeypatch):
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def base_shared_config(tmp_path):
    path = tmp_path / "shared.yaml"
    yaml.safe_dump(
        {
            "base-only": {
                "name": "Base Only",
                "tests": [
                    {
                        "name": "Base test",
                        "dataset": "test_sample_dataset",
                        "metric": {"name": "accuracy_adapter"},
                    }
                ],
            }
        },
        path.open("w"),
    )
    return path


@pytest.fixture
def extensions_dir(tmp_path):
    root = tmp_path / "benchmark-extensions"
    datasets = root / "datasets"
    datasets.mkdir(parents=True)
    shared_dir = root / "test_configs"
    shared_dir.mkdir()
    (datasets / "ext_only_dataset.json").write_text(
        '{"name":"Ext","description":"","license":"","reference":"","examples":[{"input":"x","target":"y"}]}'
    )
    yaml.safe_dump(
        {
            "extension-bundle": {
                "name": "Extension Bundle",
                "tests": [
                    {
                        "name": "Extension test",
                        "dataset": "ext_only_dataset",
                        "metric": {"name": "accuracy_adapter"},
                    }
                ],
            }
        },
        (shared_dir / "shared.yaml").open("w"),
    )
    return root


def _patch_moon807(enabled: bool):
    adapter = MagicMock()
    adapter.load_flags.return_value = {
        FeatureFlagNames.AIVET_OCT2026_MOON807: enabled,
    }
    return patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    )


@pytest.mark.integration
def test_seed_merges_extension_shared_yaml(
    test_db_env,
    base_shared_config,
    extensions_dir,
    monkeypatch,
):
    from domain.services.feature_flags import FeatureFlags

    monkeypatch.setenv("MOONSHOT_BENCHMARK_EXTENSIONS_DIR", str(extensions_dir))
    FeatureFlags._flags = None
    with _patch_moon807(True):
        FeatureFlags._flags = None
        service = SharedConfigSeedService(
            moonshot_config_repository=MoonshotConfigAdapter(),
            shared_config_repository=FileSharedConfigRepository(),
            benchmark_dataset_seed_service=BenchmarkDatasetSeedService(
                source_dataset_repository=FileDatasetRepository(),
                target_dataset_repository=SqlAlchemyDatasetRepository(),
            ),
        )
        assert service.seed_if_test_file_changed(config_path=base_shared_config) is True

        session_manager = SessionManager.get_instance()
        with session_manager.get_session() as session:
            system_names = {
                row.system_name for row in session.query(BenchmarkTestBundleModel).all()
            }
        assert "base-only" in system_names
        assert "extension-bundle" in system_names
