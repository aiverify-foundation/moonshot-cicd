import pytest
from domain.entities.benchmark_run_test_bundle_entity import \
    BenchmarkRunTestBundleEntity
from pydantic import ValidationError


class TestBenchmarkRunTestBundleEntity:
    """Tests for BenchmarkRunTestBundleEntity."""

    def test_full_required_fields(self):
        entity = BenchmarkRunTestBundleEntity(
            run_id=1,
            test_bundle_id=2,
            test_id=3,
        )
        assert entity.run_id == 1
        assert entity.test_bundle_id == 2
        assert entity.test_id == 3
        assert entity.id is None

    def test_with_id(self):
        entity = BenchmarkRunTestBundleEntity(
            id=5,
            run_id=1,
            test_bundle_id=2,
            test_id=3,
        )
        assert entity.id == 5

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            BenchmarkRunTestBundleEntity(run_id=1, test_bundle_id=2)
        with pytest.raises(ValidationError):
            BenchmarkRunTestBundleEntity(
                run_id=1,
                test_id=3,
            )
