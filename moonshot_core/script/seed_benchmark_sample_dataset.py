#!/usr/bin/env python3
"""
Seed the benchmark DB from data/datasets/test_sample_dataset.json.

Instantiates BenchmarkDatasetSeedService with FileDatasetRepository (source)
and SqlAlchemyDatasetRepository (target), then calls seed_benchmark_dataset
for the test_sample_dataset. Insert only; fails if dataset already exists.

Usage:
    cd moonshot_core
    conda activate moonshotv1test
    python script/seed_benchmark_sample_dataset.py

Prerequisites:
    - moonshot_core/data/datasets/test_sample_dataset.json exists
    - Database and migrations are set up (moonshot.db)
"""

import argparse
import sys
from pathlib import Path

# Add src to Python path (script is in moonshot_core/script/)
script_dir = Path(__file__).resolve().parent
moonshot_core_dir = script_dir.parent
src_path = moonshot_core_dir / "src"
sys.path.insert(0, str(src_path))

from application.services.benchmark_dataset_seed_service import (
    BenchmarkDatasetSeedService,
)
from application.services.file_dataset_repository import FileDatasetRepository
from adapters.driven.repository.sqlalchemy.dataset_adapter import (
    SqlAlchemyDatasetRepository,
)

DATASET_ID = "test_sample_dataset"  # filename without .json for data/datasets/test_sample_dataset.json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed benchmark DB from test_sample_dataset.json (version auto-assigned)"
    )
    args = parser.parse_args()

    source = FileDatasetRepository()
    target = SqlAlchemyDatasetRepository()
    service = BenchmarkDatasetSeedService(
        source_dataset_repository=source,
        target_dataset_repository=target,
    )

    try:
        service.seed_benchmark_dataset(DATASET_ID)
        print(f"Seeded dataset: dataset_id={DATASET_ID!r}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
