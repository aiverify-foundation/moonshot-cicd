from datetime import datetime, timezone

import pytest
from domain.entities.benchmark_run_test_status_entity import \
    BenchmarkRunTestStatusEntity
from pydantic import ValidationError


class TestBenchmarkRunTestStatusEntity:
    """Tests for BenchmarkRunTestStatusEntity."""

    def test_minimal_required_fields(self):
        entity = BenchmarkRunTestStatusEntity(
            run_id=1,
            test_id=2,
            status="not_started",
        )
        assert entity.run_id == 1
        assert entity.test_id == 2
        assert entity.status == "not_started"
        assert entity.id is None
        assert entity.start_dt is None
        assert entity.system_prompt is None

    def test_full_initialization(self):
        now = datetime.now(timezone.utc)
        entity = BenchmarkRunTestStatusEntity(
            id=10,
            run_id=1,
            test_id=2,
            status="completed",
            start_dt=now,
            end_dt=now,
            connector_pre_prompt="pre",
            connector_post_prompt="post",
            system_prompt="system",
        )
        assert entity.id == 10
        assert entity.start_dt == now
        assert entity.connector_pre_prompt == "pre"
        assert entity.system_prompt == "system"

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            BenchmarkRunTestStatusEntity(run_id=1, status="pending")
        with pytest.raises(ValidationError):
            BenchmarkRunTestStatusEntity(
                test_id=2,
                status="pending",
            )
