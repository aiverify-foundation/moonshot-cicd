import pytest
from domain.entities.benchmark_run_test_prompt_entity import \
    BenchmarkRunTestPromptEntity
from pydantic import ValidationError


class TestBenchmarkRunTestPromptEntity:
    """Tests for BenchmarkRunTestPromptEntity."""

    def test_minimal_required_fields(self):
        entity = BenchmarkRunTestPromptEntity(
            run_test_id=1,
            prompt_id=10,
            status="pending",
        )
        assert entity.run_test_id == 1
        assert entity.prompt_id == 10
        assert entity.status == "pending"
        assert entity.id is None
        assert entity.target == ""
        assert entity.prediction_result is None

    def test_full_initialization(self):
        entity = BenchmarkRunTestPromptEntity(
            id=5,
            run_test_id=1,
            prompt_id=10,
            status="completed",
            target="expected",
            prediction_result="model output",
            evaluation_accuracy=1.0,
        )
        assert entity.id == 5
        assert entity.target == "expected"
        assert entity.prediction_result == "model output"
        assert entity.evaluation_accuracy == 1.0

    def test_optional_fields_default_none(self):
        entity = BenchmarkRunTestPromptEntity(
            run_test_id=1,
            prompt_id=2,
            status="pending",
        )
        assert entity.prompt_additional_info is None
        assert entity.prediction_context is None
        assert entity.evaluation_prompt is None
        assert entity.user_evaluation is None
        assert entity.user_notes is None

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            BenchmarkRunTestPromptEntity(
                run_test_id=1,
                status="pending",
            )
