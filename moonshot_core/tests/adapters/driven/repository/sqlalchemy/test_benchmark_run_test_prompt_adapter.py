"""Unit tests for SqlAlchemyBenchmarkRunTestPromptRepository."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter import \
    SqlAlchemyBenchmarkRunTestPromptRepository
from adapters.driven.repository.sqlalchemy.llm_provider_models import \
    BenchmarkRunTestPromptModel
from domain.entities.benchmark_run_test_prompt_entity import \
    BenchmarkRunTestPromptEntity


def _make_mock_model(
    id=1,
    run_test_id=2,
    prompt_id=10,
    status="pending",
    target="",
    **kwargs,
):
    m = MagicMock(spec=BenchmarkRunTestPromptModel)
    m.id = id
    m.run_test_id = run_test_id
    m.prompt_id = prompt_id
    m.status = status
    m.target = target
    # Optional string/float/int fields - set to None so Pydantic accepts (MagicMock would fail)
    m.prompt_additional_info = None
    m.prediction_result = None
    m.prediction_context = None
    m.evaluation_prompt = None
    m.evaluation_prediction_result = None
    m.evaluation_accuracy = None
    m.user_evaluation = None
    m.user_notes = None
    for k, v in kwargs.items():
        setattr(m, k, v)
    return m


@patch(
    "adapters.driven.repository.sqlalchemy.benchmark_run_test_prompt_adapter.SessionManager"
)
class TestSqlAlchemyBenchmarkRunTestPromptRepository:
    """Tests for SqlAlchemyBenchmarkRunTestPromptRepository."""

    def test_get_all_by_run_test_id_empty(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        result = repo.get_all_by_run_test_id(5)

        assert result == []
        mock_session.query.assert_called_once_with(BenchmarkRunTestPromptModel)
        mock_session.query.return_value.filter.return_value.all.assert_called_once()

    def test_get_all_by_run_test_id_returns_entities(self, mock_sm_class):
        mock_model = _make_mock_model(
            id=1,
            run_test_id=5,
            prompt_id=10,
            status="completed",
            target="t",
            prediction_result="out",
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_model
        ]
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        result = repo.get_all_by_run_test_id(5)

        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].run_test_id == 5
        assert result[0].prompt_id == 10
        assert result[0].status == "completed"
        assert result[0].target == "t"
        assert result[0].prediction_result == "out"

    def test_get_by_id_returns_entity(self, mock_sm_class):
        mock_model = _make_mock_model(
            id=7,
            run_test_id=3,
            prompt_id=10,
            status="completed",
            target="t",
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        result = repo.get_by_id(7)

        assert result is not None
        assert result.id == 7
        mock_session.query.assert_called_once_with(BenchmarkRunTestPromptModel)
        mock_session.query.return_value.filter.assert_called_once()

    def test_get_by_id_not_found(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        assert repo.get_by_id(1) is None

    def test_save_insert_returns_entity_with_id(self, mock_sm_class):
        mock_session = MagicMock()

        def set_id_on_add(model):
            model.id = 42

        mock_session.add.side_effect = set_id_on_add
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        entity = BenchmarkRunTestPromptEntity(
            run_test_id=1,
            prompt_id=2,
            status="pending",
        )
        saved = repo.save(entity)

        assert saved.id == 42
        assert saved.run_test_id == 1
        assert saved.prompt_id == 2
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_save_with_id_raises(self, mock_sm_class):
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=MagicMock())
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        entity = BenchmarkRunTestPromptEntity(
            id=10,
            run_test_id=1,
            prompt_id=2,
            status="completed",
            target="new",
        )
        with pytest.raises(ValueError, match="Cannot save: entity has id set"):
            repo.save(entity)

    def test_update_returns_entity(self, mock_sm_class):
        mock_model = _make_mock_model(
            id=10,
            run_test_id=1,
            prompt_id=2,
            status="pending",
            target="old",
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        entity = BenchmarkRunTestPromptEntity(
            id=10,
            run_test_id=1,
            prompt_id=2,
            status="completed",
            target="new",
        )
        result = repo.update(entity)

        assert result.id == 10
        assert result.status == "completed"
        assert result.target == "new"
        mock_session.flush.assert_called_once()

    def test_update_not_found_raises(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestPromptRepository()
        entity = BenchmarkRunTestPromptEntity(
            id=999,
            run_test_id=1,
            prompt_id=2,
            status="completed",
        )
        with pytest.raises(ValueError, match="no benchmark_run_test_prompt"):
            repo.update(entity)
