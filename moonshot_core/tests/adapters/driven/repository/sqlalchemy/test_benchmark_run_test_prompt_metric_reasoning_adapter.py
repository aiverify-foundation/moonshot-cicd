"""Tests for SqlAlchemyBenchmarkRunTestPromptMetricReasoningRepository."""

import pytest
from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_metric_reasoning_adapter import (
    SqlAlchemyBenchmarkRunTestPromptMetricReasoningRepository,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunModel,
    BenchmarkRunTestPromptMetricReasoningModel,
    BenchmarkRunTestPromptModel,
    BenchmarkRunTestStatusModel,
    BenchmarkTestDatasetModel,
    BenchmarkTestDatasetPromptModel,
    BenchmarkTestMetricModel,
    BenchmarkTestModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Repository bound to a fresh migrated SQLite file."""
    db_path = tmp_path / "metric_reasoning.db"
    monkeypatch.setenv("MOONSHOT_DB_PATH", str(db_path))
    SessionManager.reset_instance()
    repository = SqlAlchemyBenchmarkRunTestPromptMetricReasoningRepository()
    yield repository
    SessionManager.reset_instance()


def _seed_run_prompts(count: int) -> list[int]:
    """Insert the parent rows for ``count`` benchmark_run_test_prompt rows."""
    with SessionManager.get_instance().get_session() as session:
        dataset = BenchmarkTestDatasetModel(
            version=1, system_name="metric_reasoning_ds"
        )
        session.add(dataset)
        session.flush()

        metric = BenchmarkTestMetricModel(name="metric_reasoning_metric")
        session.add(metric)
        session.flush()

        test = BenchmarkTestModel(
            version=1,
            system_name="metric_reasoning_test",
            name="Metric reasoning test",
            type="benchmark",
            dataset_id=dataset.id,
            metric_id=metric.id,
        )
        session.add(test)
        session.flush()

        run = BenchmarkRunModel(
            name="metric reasoning run",
            status="completed",
            endpoint_type="LLM_Provider",
        )
        session.add(run)
        session.flush()

        status = BenchmarkRunTestStatusModel(
            run_id=run.id,
            test_id=test.id,
            status="completed",
        )
        session.add(status)
        session.flush()

        prompt_ids: list[int] = []
        for index in range(count):
            dataset_prompt = BenchmarkTestDatasetPromptModel(
                benchmark_test_dataset_id=dataset.id,
                prompt=f"prompt {index}",
                target=f"target {index}",
            )
            session.add(dataset_prompt)
            session.flush()
            row = BenchmarkRunTestPromptModel(
                run_test_id=status.id,
                prompt_id=dataset_prompt.id,
                status="completed",
                target=f"target {index}",
            )
            session.add(row)
            session.flush()
            prompt_ids.append(row.id)
        return prompt_ids


def _reasoning_row_count() -> int:
    with SessionManager.get_instance().get_session() as session:
        return session.query(BenchmarkRunTestPromptMetricReasoningModel).count()


class TestSqlAlchemyBenchmarkRunTestPromptMetricReasoningRepository:
    def test_add_twice_keeps_both_and_latest_is_second(self, repo):
        prompt_id = _seed_run_prompts(1)[0]

        first = repo.add_metric_reasoning(prompt_id, "first reasoning")
        second = repo.add_metric_reasoning(prompt_id, "  second reasoning  ")

        assert _reasoning_row_count() == 2
        assert first.id is not None
        assert second.id is not None
        assert second.id > first.id
        assert second.reasoning == "  second reasoning  "
        assert second.create_dt is not None

        latest = repo.get_latest_metric_reasoning(prompt_id)
        assert latest is not None
        assert latest.id == second.id
        assert latest.reasoning == "  second reasoning  "
        assert latest.benchmark_run_test_prompt_id == prompt_id

    def test_get_latest_returns_none_when_prompt_has_no_rows(self, repo):
        prompt_id = _seed_run_prompts(1)[0]
        assert repo.get_latest_metric_reasoning(prompt_id) is None

    @pytest.mark.parametrize("reasoning", [None, "", "   "])
    def test_add_rejects_blank_reasoning_and_writes_nothing(self, repo, reasoning):
        prompt_id = _seed_run_prompts(1)[0]
        with pytest.raises(ValueError):
            repo.add_metric_reasoning(prompt_id, reasoning)
        assert _reasoning_row_count() == 0

    def test_batch_returns_latest_per_prompt_and_omits_missing(self, repo):
        first_id, second_id, empty_id = _seed_run_prompts(3)
        repo.add_metric_reasoning(first_id, "first older")
        newer = repo.add_metric_reasoning(first_id, "first newer")
        only = repo.add_metric_reasoning(second_id, "second only")

        result = repo.get_latest_metric_reasoning_for_prompts(
            [first_id, second_id, empty_id]
        )

        assert set(result.keys()) == {first_id, second_id}
        assert result[first_id].id == newer.id
        assert result[first_id].reasoning == "first newer"
        assert result[second_id].id == only.id
        assert result[second_id].reasoning == "second only"
        assert empty_id not in result

    def test_batch_empty_input_returns_empty_dict(self, repo):
        assert repo.get_latest_metric_reasoning_for_prompts([]) == {}
