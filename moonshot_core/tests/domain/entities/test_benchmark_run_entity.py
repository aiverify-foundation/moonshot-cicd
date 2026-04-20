from datetime import datetime, timezone

import pytest
from domain.entities.benchmark_run_entity import BenchmarkRunEntity
from pydantic import ValidationError


class TestBenchmarkRunEntity:
    """Tests for BenchmarkRunEntity."""

    def test_minimal_required_fields(self):
        entity = BenchmarkRunEntity(
            name="run-1",
            status="running",
            endpoint_type="LLM_Provider",
        )
        assert entity.name == "run-1"
        assert entity.status == "running"
        assert entity.endpoint_type == "LLM_Provider"
        assert entity.id is None
        assert entity.start_time is None
        assert entity.llm_provider_id is None

    def test_full_initialization(self):
        now = datetime.now(timezone.utc)
        entity = BenchmarkRunEntity(
            id=1,
            name="run-1",
            status="completed",
            endpoint_type="LLM_Provider",
            start_time=now,
            end_time=now,
            llm_provider_id=2,
            llm_provider_model_id=3,
            llm_provider_model_config_id=4,
        )
        assert entity.id == 1
        assert entity.start_time == now
        assert entity.llm_provider_id == 2
        assert entity.llm_provider_model_id == 3
        assert entity.llm_provider_model_config_id == 4

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            BenchmarkRunEntity(name="run-1", status="running")
        with pytest.raises(ValidationError):
            BenchmarkRunEntity(
                name="run-1",
                endpoint_type="LLM_Provider",
            )
