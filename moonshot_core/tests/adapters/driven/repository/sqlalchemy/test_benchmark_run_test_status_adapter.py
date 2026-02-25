"""Unit tests for SqlAlchemyBenchmarkRunTestStatusRepository."""

from unittest.mock import MagicMock, patch

import pytest
from adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter import \
    SqlAlchemyBenchmarkRunTestStatusRepository
from adapters.driven.repository.sqlalchemy.llm_provider_models import \
    BenchmarkRunTestStatusModel
from domain.entities.benchmark_run_test_status_entity import \
    BenchmarkRunTestStatusEntity


def _make_mock_status_model(
    id=1,
    run_id=1,
    test_id=2,
    status="not_started",
    **kwargs,
):
    m = MagicMock(spec=BenchmarkRunTestStatusModel)
    m.id = id
    m.run_id = run_id
    m.test_id = test_id
    m.status = status
    m.start_dt = None
    m.end_dt = None
    m.connector_pre_prompt = None
    m.connector_post_prompt = None
    m.system_prompt = None
    for k, v in kwargs.items():
        setattr(m, k, v)
    return m


def _session_ctx(mock_session):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_session)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


@patch(
    "adapters.driven.repository.sqlalchemy.benchmark_run_test_status_adapter.SessionManager"
)
class TestSqlAlchemyBenchmarkRunTestStatusRepository:
    """Tests for SqlAlchemyBenchmarkRunTestStatusRepository."""

    def test_get_by_id_not_found(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        assert repo.get_by_id(999) is None

    def test_get_by_id_found(self, mock_sm_class):
        mock_model = _make_mock_status_model(
            id=10,
            run_id=1,
            test_id=2,
            status="completed",
            system_prompt="sys",
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        result = repo.get_by_id(10)
        assert result is not None
        assert result.id == 10
        assert result.run_id == 1
        assert result.test_id == 2
        assert result.status == "completed"
        assert result.system_prompt == "sys"

    def test_get_all_by_run_id_empty(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        assert repo.get_all_by_run_id(1) == []

    def test_get_all_by_run_id_returns_entities(self, mock_sm_class):
        mock_model = _make_mock_status_model(id=1, run_id=5, test_id=2)
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_model
        ]
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        result = repo.get_all_by_run_id(5)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].run_id == 5

    def test_save_insert_returns_entity_with_id(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.add.side_effect = lambda m: setattr(m, "id", 20)
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        entity = BenchmarkRunTestStatusEntity(
            run_id=1,
            test_id=2,
            status="in_progress",
        )
        saved = repo.save(entity)
        assert saved.id == 20
        assert saved.run_id == 1
        mock_session.add.assert_called_once()

    def test_save_with_id_raises(self, mock_sm_class):
        mock_session = MagicMock()
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        entity = BenchmarkRunTestStatusEntity(
            id=999,
            run_id=1,
            test_id=2,
            status="completed",
        )
        with pytest.raises(ValueError, match="Cannot save: entity has id set"):
            repo.save(entity)

    def test_update_returns_entity(self, mock_sm_class):
        mock_model = _make_mock_status_model(
            id=1,
            run_id=1,
            test_id=2,
            status="in_progress",
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        entity = BenchmarkRunTestStatusEntity(
            id=1,
            run_id=1,
            test_id=2,
            status="completed",
        )
        result = repo.update(entity)
        assert result.id == 1
        assert result.status == "completed"

    def test_update_not_found_raises(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestStatusRepository()
        entity = BenchmarkRunTestStatusEntity(
            id=999,
            run_id=1,
            test_id=2,
            status="completed",
        )
        with pytest.raises(ValueError, match="no benchmark_run_test_status"):
            repo.update(entity)
