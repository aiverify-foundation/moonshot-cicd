#!/usr/bin/env python3
"""
Integration script to run conditional shared config seed (seed only when
shared.yaml is newer than stored test_file_last_modified).

Use this to verify the flow; you can remove this file when no longer needed.

Usage:
    cd moonshot_core
    conda activate moonshotv1test
    python script/run_conditional_shared_config_seed.py

Prerequisites:
    - data/test_configs/shared.yaml exists
    - Database and migrations are set up (moonshot.db)
    - Datasets referenced in shared.yaml exist under data/datasets/ (e.g. test_sample_dataset.json)
      or are already in the DB (skipped with "already exists")
"""

import sys
from pathlib import Path

# Add src to Python path (script is in moonshot_core/script/)
script_dir = Path(__file__).resolve().parent
moonshot_core_dir = script_dir.parent
src_path = moonshot_core_dir / "src"
sys.path.insert(0, str(src_path))

from application.services.conditional_shared_config_seed_service import (
    ConditionalSharedConfigSeedService,
)
from application.services.file_shared_config_repository import FileSharedConfigRepository
from application.services.benchmark_dataset_seed_service import BenchmarkDatasetSeedService
from application.services.file_dataset_repository import FileDatasetRepository
from application.services.shared_config_seed_service import SharedConfigSeedService
from adapters.driven.repository.sqlalchemy.dataset_adapter import (
    SqlAlchemyDatasetRepository,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import (
    MoonshotConfigAdapter,
)


def main() -> int:
    moonshot_config = MoonshotConfigAdapter()
    shared_config_repo = FileSharedConfigRepository()
    dataset_seed = BenchmarkDatasetSeedService(
        source_dataset_repository=FileDatasetRepository(),
        target_dataset_repository=SqlAlchemyDatasetRepository(),
    )
    shared_config_seed = SharedConfigSeedService()

    service = ConditionalSharedConfigSeedService(
        moonshot_config_repository=moonshot_config,
        shared_config_repository=shared_config_repo,
        benchmark_dataset_seed_service=dataset_seed,
        shared_config_seed_service=shared_config_seed,
    )

    try:
        did_seed = service.seed_if_test_file_changed()
        if did_seed:
            print("Seeding ran: datasets and bundles/tests/groupings updated.")
        else:
            print("Skipped: shared.yaml not changed since last seed.")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
