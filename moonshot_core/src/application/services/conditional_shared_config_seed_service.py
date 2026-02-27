"""
Orchestrator that seeds shared config (datasets, then bundles/tests/groupings)
only when the test config file has changed, using moonshot_config last-modified check.
"""

from pathlib import Path
from typing import Optional

from application.ports.moonshot_config_repository import MoonshotConfigRepository
from application.ports.shared_config_repository import SharedConfigRepository
from application.services.benchmark_dataset_seed_service import BenchmarkDatasetSeedService
from application.services.shared_config_seed_service import SharedConfigSeedService
from domain.services.app_config import AppConfig
from domain.services.logger import configure_logger
from application.services.utils import get_application_root_path


TEST_FILE_LAST_MODIFIED_KEY = "test_file_last_modified"
DEFAULT_VERSION = 1


def _default_config_path() -> Path:
    """Return default path to shared.yaml under data/test_configs."""
    root = get_application_root_path()
    app_config = AppConfig()
    source = app_config.get_benchmark_source()
    if source.endswith(".yaml") or source.endswith(".yml"):
        config_dir = root / AppConfig.DEFAULT_DATA_PATH / "test_configs"
        return config_dir / source
    return (
        Path(source)
        if source
        else root
        / AppConfig.DEFAULT_DATA_PATH
        / "test_configs"
        / AppConfig.DEFAULT_BENCHMARK_SOURCE
    )


class ConditionalSharedConfigSeedService:
    """
    Seeds datasets and then bundles/tests/groupings from shared.yaml only when
    the config file's last-modified time is newer than the value stored in
    moonshot_config under key test_file_last_modified. Not exposed as an API.
    """

    def __init__(
        self,
        moonshot_config_repository: MoonshotConfigRepository,
        shared_config_repository: SharedConfigRepository,
        benchmark_dataset_seed_service: BenchmarkDatasetSeedService,
        shared_config_seed_service: SharedConfigSeedService,
    ) -> None:
        self.moonshot_config = moonshot_config_repository
        self.shared_config_repo = shared_config_repository
        self.dataset_seed_service = benchmark_dataset_seed_service
        self.shared_config_seed_service = shared_config_seed_service
        self.logger = configure_logger(__name__)

    def seed_if_test_file_changed(
        self,
        config_path: Optional[Path] = None,
        version: int = DEFAULT_VERSION,
    ) -> bool:
        """
        If the test config file is newer than the stored last-modified value,
        seed datasets then bundles/tests/groupings and update the stored value.
        Otherwise do nothing.

        Args:
            config_path: Path to shared.yaml. If None, uses default from AppConfig.
            version: Version for datasets and bundle/test rows; default 1.

        Returns:
            True if seeding was performed, False if skipped (file unchanged).
        """
        path = config_path or _default_config_path()
        try:
            mtime = self.shared_config_repo.get_last_modified(path)
        except FileNotFoundError:
            self.logger.warning("Config file not found: %s, skipping seed", path)
            return False

        entity = self.moonshot_config.get_by_key(TEST_FILE_LAST_MODIFIED_KEY)
        if entity and entity.value is not None and entity.value.strip():
            try:
                stored = float(entity.value)
            except ValueError:
                stored = 0.0
            if stored >= mtime:
                self.logger.debug(
                    "Test config file unchanged (stored=%s >= mtime=%s), skip seed",
                    stored,
                    mtime,
                )
                return False

        self.logger.info("Test config file changed or first run, seeding from %s", path)
        config = self.shared_config_repo.get_config(path)

        # Collect unique dataset names from config
        dataset_names: set[str] = set()
        for bundle_data in config.values():
            if not isinstance(bundle_data, dict):
                continue
            for test in bundle_data.get("tests") or []:
                if isinstance(test, dict) and test.get("dataset"):
                    dataset_names.add(test["dataset"])

        for name in sorted(dataset_names):
            try:
                self.dataset_seed_service.seed_benchmark_dataset(name)
            except ValueError as e:
                if "already exists" in str(e).lower():
                    self.logger.debug("Dataset already exists: %r, skipping", name)
                else:
                    self.logger.warning(
                        "Could not seed dataset %r: %s",
                        name,
                        e,
                        exc_info=False,
                    )

        self.shared_config_seed_service.seed_from_data(
            config, config_path=path, version=version
        )
        self.moonshot_config.set(TEST_FILE_LAST_MODIFIED_KEY, str(mtime))
        self.logger.info("Seeding complete, updated %s", TEST_FILE_LAST_MODIFIED_KEY)
        return True
