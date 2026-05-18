"""Tests for TestDetailsLoader."""

from pathlib import Path

import pytest

from application.services.test_details_loader import (
    TestDetailsLoader,
    dataset_system_name_for_details,
)

MOONSHOT_CORE_ROOT = Path(__file__).resolve().parents[3]
REAL_CSV = MOONSHOT_CORE_ROOT / "data" / "test_details" / "test_details.csv"

_EXPECTED_COLUMNS = {
    "category_name",
    "dataset",
    "hazard",
    "input",
    "target",
    "response",
    "evaluator_verdict",
}


class TestTestDetailsLoader:
    def test_load_real_csv_strips_row_id_and_indexes_by_dataset(self):
        loader = TestDetailsLoader(csv_path=REAL_CSV)
        rows = loader.get_rows_for_dataset("mlc-ailuminate-vcr")

        assert rows is not None
        assert len(rows) == 2
        for row in rows:
            assert "row_id" not in row
            assert set(row.keys()) == _EXPECTED_COLUMNS
            assert row["dataset"] == "mlc-ailuminate-vcr"

    def test_get_rows_for_datasets_concatenates_unique_datasets(self):
        loader = TestDetailsLoader(csv_path=REAL_CSV)
        rows = loader.get_rows_for_datasets(
            ["mlc-ailuminate-vcr", "mlc-ailuminate-ncr", "mlc-ailuminate-vcr"]
        )

        assert rows is not None
        assert len(rows) == 4
        datasets = {r["dataset"] for r in rows}
        assert datasets == {"mlc-ailuminate-vcr", "mlc-ailuminate-ncr"}

    def test_unknown_dataset_returns_none(self):
        loader = TestDetailsLoader(csv_path=REAL_CSV)
        assert loader.get_rows_for_dataset("nonexistent-dataset") is None

    def test_empty_datasets_iterable_returns_none(self):
        loader = TestDetailsLoader(csv_path=REAL_CSV)
        assert loader.get_rows_for_datasets([]) is None

    def test_missing_file_returns_empty_index(self, tmp_path):
        loader = TestDetailsLoader(csv_path=tmp_path / "missing.csv")
        assert loader.get_rows_for_dataset("any") is None
        assert loader.get_rows_for_datasets(["any"]) is None

    def test_dataset_system_name_for_details(self):
        assert (
            dataset_system_name_for_details("mlc-ailuminate-vcr", "Display Name")
            == "mlc-ailuminate-vcr"
        )
        assert (
            dataset_system_name_for_details("42", "mlc-ailuminate-vcr")
            == "mlc-ailuminate-vcr"
        )

    def test_custom_csv_via_tmp_path(self, tmp_path):
        csv_path = tmp_path / "test_details.csv"
        csv_path.write_text(
            "row_id,category_name,dataset,hazard,input,target,response,evaluator_verdict\n"
            '0,Cat A,ds-a,h1,"line one\nline two",t1,r1,1\n'
            "1,Cat B,ds-b,h2,input2,t2,r2,0\n",
            encoding="utf-8",
        )
        loader = TestDetailsLoader(csv_path=csv_path)
        rows_a = loader.get_rows_for_dataset("ds-a")

        assert rows_a is not None
        assert len(rows_a) == 1
        assert rows_a[0]["input"] == "line one\nline two"
        assert "row_id" not in rows_a[0]
