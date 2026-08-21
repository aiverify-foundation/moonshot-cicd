"""Load test detail rows from data/test_details/test_details.csv keyed by dataset."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Optional

from application.services.utils import get_application_root_path
from domain.services.app_config import AppConfig
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

_ROW_ID_COLUMN = "row_id"
_DEFAULT_CSV_NAME = "test_details.csv"


def dataset_system_name_for_details(dataset_id: str, dataset_name: str) -> str:
    """
    Resolve the YAML/CSV dataset key for test_details lookup.

    File-backed datasets use the loader filename as ``id`` (e.g. mlc-ailuminate-vcr).
    DB-backed datasets use numeric ``id`` and store system_name in ``name``.
    """
    if dataset_id and not dataset_id.isdigit():
        return dataset_id
    return dataset_name or ""


class TestDetailsLoader:
    """Reads and caches test_details.csv rows indexed by the dataset column."""

    def __init__(self, csv_path: Optional[Path] = None) -> None:
        root = get_application_root_path()
        self._csv_path = csv_path or (
            root / AppConfig.DEFAULT_TEST_DETAILS_PATH / _DEFAULT_CSV_NAME
        )

    def get_rows_for_dataset(self, dataset_system_name: str) -> Optional[list[dict[str, str]]]:
        """Return rows for one dataset system name, or None if none match."""
        if not dataset_system_name:
            return None
        index = self._load_index()
        rows = index.get(dataset_system_name)
        if not rows:
            return None
        return list(rows)

    def get_rows_for_datasets(
        self, dataset_system_names: Iterable[str]
    ) -> Optional[list[dict[str, str]]]:
        """Return concatenated rows for all given datasets, or None if none match."""
        index = self._load_index()
        seen: set[str] = set()
        combined: list[dict[str, str]] = []
        for name in dataset_system_names:
            if not name or name in seen:
                continue
            seen.add(name)
            combined.extend(index.get(name, []))
        return combined if combined else None

    @lru_cache(maxsize=1)
    def _load_index(self) -> dict[str, list[dict[str, str]]]:
        if not self._csv_path.is_file():
            logger.warning("Test details CSV not found: %s", self._csv_path)
            return {}

        index: dict[str, list[dict[str, str]]] = {}
        with self._csv_path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                dataset_key = (row.get("dataset") or "").strip()
                if not dataset_key:
                    continue
                cleaned = {k: v for k, v in row.items() if k != _ROW_ID_COLUMN}
                index.setdefault(dataset_key, []).append(cleaned)

        return index
