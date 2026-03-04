"""
Service that seeds benchmark_test_bundle, benchmark_test, and benchmark_test_bundle_grouping
from shared.yaml.

Reads the YAML config, resolves dataset and metric references, and inserts or updates the three
SQLAlchemy entities via BenchmarkTestConfigAdapter. Datasets must already exist in
benchmark_test_dataset (e.g. seeded via BenchmarkDatasetSeedService).

When moonshot_config_repository, shared_config_repository, and benchmark_dataset_seed_service
are provided at construction, seed_if_test_file_changed() can be used to seed only when the
config file has changed (mtime check), seeding datasets first then bundles/tests/groupings.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml

from domain.services.logger import configure_logger
from domain.services.app_config import AppConfig
from application.services.utils import get_application_root_path
from adapters.driven.repository.sqlalchemy.benchmark_test_config_adapter import (
    BenchmarkTestConfigAdapter,
)

if TYPE_CHECKING:
    from application.ports.moonshot_config_repository import MoonshotConfigRepository
    from application.ports.shared_config_repository import SharedConfigRepository
    from application.services.benchmark_dataset_seed_service import (
        BenchmarkDatasetSeedService,
    )

TEST_FILE_LAST_MODIFIED_KEY = "test_file_last_modified"


def _slug(text: str) -> str:
    """Return a safe identifier: lowercase, non-alphanumeric replaced with single underscore."""
    if not text:
        return ""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


class SharedConfigSeedService:
    """
    Seeds benchmark_test_bundle, benchmark_test, and benchmark_test_bundle_grouping
    from shared.yaml.

    Loads and parses the YAML file, then for each bundle and test inserts or updates the
    corresponding DB rows and groupings. Uses version=1. Referenced datasets must
    already exist in benchmark_test_dataset (or use seed_if_test_file_changed to seed
    datasets first when the three optional dependencies are provided).
    """

    DEFAULT_VERSION = 1

    def __init__(
        self,
        adapter: Optional[BenchmarkTestConfigAdapter] = None,
        moonshot_config_repository: Optional["MoonshotConfigRepository"] = None,
        shared_config_repository: Optional["SharedConfigRepository"] = None,
        benchmark_dataset_seed_service: Optional["BenchmarkDatasetSeedService"] = None,
    ) -> None:
        self.adapter = adapter or BenchmarkTestConfigAdapter()
        self._moonshot_config = moonshot_config_repository
        self._shared_config_repo = shared_config_repository
        self._dataset_seed_service = benchmark_dataset_seed_service
        self.logger = configure_logger(__name__)

    def _default_config_path(self) -> Path:
        """Return default path to shared.yaml under data/test_configs."""
        root = get_application_root_path()
        app_config = AppConfig()
        # get_benchmark_source() returns filename (e.g. shared.yaml) or env path
        source = app_config.get_benchmark_source()
        if source.endswith(".yaml") or source.endswith(".yml"):
            config_dir = root / AppConfig.DEFAULT_DATA_PATH / "test_configs"
            return config_dir / source
        return Path(source) if source else root / AppConfig.DEFAULT_DATA_PATH / "test_configs" / AppConfig.DEFAULT_BENCHMARK_SOURCE

    def _load_config(self, config_path: Path) -> dict[str, Any]:
        """Load and parse YAML from config_path. Raises on invalid structure."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Expected top-level dict in {config_path}, got {type(data).__name__}")
        return data

    def seed_from_config(
        self,
        config_path: Optional[Path] = None,
        version: int = DEFAULT_VERSION,
    ) -> None:
        """
        Load shared config from YAML and insert or update benchmark_test_bundle, benchmark_test,
        and benchmark_test_bundle_grouping.

        Args:
            config_path: Path to shared.yaml. If None, uses default from AppConfig
                (data/test_configs/shared.yaml under application root).
            version: Version number for bundle and test rows; default 1.

        Raises:
            FileNotFoundError: If config_path does not exist.
            ValueError: If YAML is not a dict or a referenced dataset system_name
                is not found in benchmark_test_dataset.
        """
        path = config_path or self._default_config_path()
        self.logger.info("Seeding shared config from %s", path)
        data = self._load_config(path)
        self._seed_from_data(data, path, version)

    def seed_from_data(
        self,
        data: dict[str, Any],
        config_path: Optional[Path] = None,
        version: int = DEFAULT_VERSION,
    ) -> None:
        """
        Insert or update benchmark_test_bundle, benchmark_test, and
        benchmark_test_bundle_grouping from an already-loaded config dict.

        Args:
            data: Parsed config (same shape as from shared.yaml).
            config_path: Optional path for logging only.
            version: Version number for bundle and test rows; default 1.

        Raises:
            ValueError: If a referenced dataset system_name is not found in
                benchmark_test_dataset.
        """
        if config_path is not None:
            self.logger.info("Seeding shared config from data (path=%s)", config_path)
        else:
            self.logger.info("Seeding shared config from data")
        self._seed_from_data(data, config_path, version)

    def seed_if_test_file_changed(
        self,
        config_path: Optional[Path] = None,
        version: int = DEFAULT_VERSION,
    ) -> bool:
        """
        If the test config file is newer than the stored last-modified value,
        seed datasets then bundles/tests/groupings and update the stored value.
        Otherwise do nothing. Requires moonshot_config_repository,
        shared_config_repository, and benchmark_dataset_seed_service at construction.

        Args:
            config_path: Path to shared.yaml. If None, uses default from AppConfig.
            version: Version for datasets and bundle/test rows; default 1.

        Returns:
            True if seeding was performed, False if skipped (file unchanged or not found).

        Raises:
            ValueError: If any of the three optional dependencies was not provided.
        """
        if (
            self._moonshot_config is None
            or self._shared_config_repo is None
            or self._dataset_seed_service is None
        ):
            raise ValueError(
                "seed_if_test_file_changed requires moonshot_config_repository, "
                "shared_config_repository, and benchmark_dataset_seed_service to be "
                "provided at construction."
            )
        path = config_path or self._default_config_path()
        try:
            mtime = self._shared_config_repo.get_last_modified(path)
        except FileNotFoundError:
            self.logger.warning("Config file not found: %s, skipping seed", path)
            return False

        entity = self._moonshot_config.get_by_key(TEST_FILE_LAST_MODIFIED_KEY)
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
        config = self._shared_config_repo.get_config(path)

        dataset_names: set[str] = set()
        for bundle_data in config.values():
            if not isinstance(bundle_data, dict):
                continue
            for test in bundle_data.get("tests") or []:
                if isinstance(test, dict) and test.get("dataset"):
                    dataset_names.add(test["dataset"])

        for name in sorted(dataset_names):
            try:
                self._dataset_seed_service.seed_benchmark_dataset(name)
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

        self._seed_from_data(config, path, version)
        self._moonshot_config.set(TEST_FILE_LAST_MODIFIED_KEY, str(mtime))
        self.logger.info("Seeding complete, updated %s", TEST_FILE_LAST_MODIFIED_KEY)
        return True

    def _seed_from_data(
        self,
        data: dict[str, Any],
        config_path: Optional[Path],
        version: int,
    ) -> None:
        """Common logic: metrics, then bundles, tests, and groupings from data."""
        # Collect all unique metric names and ensure metrics exist
        metric_names: set[str] = set()
        for bundle_key, bundle_data in data.items():
            if not isinstance(bundle_data, dict):
                continue
            tests = bundle_data.get("tests") or []
            for test in tests:
                if not isinstance(test, dict):
                    continue
                metric = test.get("metric")
                if isinstance(metric, dict) and metric.get("name"):
                    metric_names.add(metric["name"])
        for name in sorted(metric_names):
            self.adapter.get_or_create_metric(name)

        # Insert or update bundles, tests, and groupings
        for bundle_key, bundle_data in data.items():
            if not isinstance(bundle_data, dict):
                self.logger.warning("Skipping non-dict bundle entry: %r", bundle_key)
                continue
            tests = bundle_data.get("tests")
            if not tests:
                self.logger.debug("Bundle %r has no tests, skipping", bundle_key)
                continue

            name = bundle_data.get("name", bundle_key)
            description = bundle_data.get("description")
            if description is not None and not isinstance(description, str):
                description = str(description)
            category = bundle_data.get("category", "")

            bundle_id = self.adapter.get_bundle_id(version=version, system_name=bundle_key)
            if bundle_id is not None:
                bundle_id = self.adapter.update_bundle(
                    version=version,
                    system_name=bundle_key,
                    name=name,
                    description=description,
                    category=category,
                )
            else:
                bundle_id = self.adapter.insert_bundle(
                    version=version,
                    system_name=bundle_key,
                    name=name,
                    description=description,
                    category=category,
                )

            for test in tests:
                if not isinstance(test, dict):
                    continue
                test_name = test.get("name")
                if not test_name:
                    self.logger.warning("Test missing 'name' in bundle %r, skipping", bundle_key)
                    continue
                dataset_system_name = test.get("dataset")
                if not dataset_system_name:
                    raise ValueError(
                        f"Test {test_name!r} in bundle {bundle_key!r} has no 'dataset'. "
                        "Each test must specify a dataset system_name."
                    )
                metric = test.get("metric") or {}
                if not isinstance(metric, dict):
                    metric = {}
                metric_name = metric.get("name")
                if not metric_name:
                    raise ValueError(
                        f"Test {test_name!r} in bundle {bundle_key!r} has no 'metric.name'. "
                        "Each test must specify a metric name."
                    )

                dataset_id = self.adapter.get_dataset_id_by_system_name_latest(
                    dataset_system_name,
                )
                metric_id = self.adapter.get_or_create_metric(metric_name)
                test_system_name = f"{bundle_key}__{_slug(test_name)}"
                type_ = test.get("type", "benchmark")

                test_id = self.adapter.get_test_id(version=version, system_name=test_system_name)
                if test_id is not None:
                    test_id = self.adapter.update_test(
                        version=version,
                        system_name=test_system_name,
                        name=test_name,
                        type_=type_,
                        dataset_id=dataset_id,
                        metric_id=metric_id,
                    )
                else:
                    test_id = self.adapter.insert_test(
                        version=version,
                        system_name=test_system_name,
                        name=test_name,
                        type_=type_,
                        dataset_id=dataset_id,
                        metric_id=metric_id,
                    )
                if not self.adapter.grouping_exists(test_bundle_id=bundle_id, test_id=test_id):
                    self.adapter.insert_grouping(test_bundle_id=bundle_id, test_id=test_id)

        if config_path is not None:
            self.logger.info("Finished seeding shared config from %s", config_path)
        else:
            self.logger.info("Finished seeding shared config from data")
