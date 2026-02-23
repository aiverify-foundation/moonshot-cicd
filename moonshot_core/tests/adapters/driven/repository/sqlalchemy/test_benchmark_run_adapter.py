"""Unit tests for SqlAlchemyBenchmarkRunRepository."""

from unittest.mock import MagicMock, patch

import pytest
from adapters.driven.repository.sqlalchemy.benchmark_run_adapter import \
    SqlAlchemyBenchmarkRunRepository
from adapters.driven.repository.sqlalchemy.llm_provider_models import \
    BenchmarkRunModel
from domain.entities.benchmark_run_entity import BenchmarkRunEntity


def _make_mock_run_model(
    id=1,
    name="run-1",
    status="running",
    endpoint_type="LLM_Provider",
    **kwargs,
):
    m = MagicMock(spec=BenchmarkRunModel)
    m.id = id
    m.name = name
    m.status = status
    m.endpoint_type = endpoint_type
    for k, v in kwargs.items():
        setattr(m, k, v)
    return m


def _session_ctx(mock_session):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_session)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


@patch("adapters.driven.repository.sqlalchemy.benchmark_run_adapter.SessionManager")
class TestSqlAlchemyBenchmarkRunRepository:
    """Tests for SqlAlchemyBenchmarkRunRepository."""

    def test_get_by_id_not_found(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        assert repo.get_by_id(999) is None

    def test_get_by_id_found(self, mock_sm_class):
        mock_model = _make_mock_run_model(
            id=1,
            name="run-1",
            status="completed",
            llm_provider_id=2,
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        result = repo.get_by_id(1)
        assert result is not None
        assert result.id == 1
        assert result.name == "run-1"
        assert result.status == "completed"
        assert result.llm_provider_id == 2

    def test_get_by_name_not_found(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        assert repo.get_by_name("missing") is None

    def test_get_by_name_found(self, mock_sm_class):
        mock_model = _make_mock_run_model(name="my-run")
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        result = repo.get_by_name("my-run")
        assert result is not None
        assert result.name == "my-run"

    def test_get_all_empty(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = []
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        assert repo.get_all() == []

    def test_get_all_returns_entities(self, mock_sm_class):
        mock_model = _make_mock_run_model(id=1, name="run-1")
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = [mock_model]
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        result = repo.get_all()
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].name == "run-1"

    def test_save_insert_returns_entity_with_id(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.add.side_effect = lambda m: setattr(m, "id", 7)
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        entity = BenchmarkRunEntity(
            name="new-run",
            status="running",
            endpoint_type="LLM_Provider",
        )
        saved = repo.save(entity)
        assert saved.id == 7
        assert saved.name == "new-run"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_save_update_returns_entity(self, mock_sm_class):
        mock_model = _make_mock_run_model(
            id=1,
            name="old",
            status="running",
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        entity = BenchmarkRunEntity(
            id=1,
            name="updated",
            status="completed",
            endpoint_type="LLM_Provider",
        )
        saved = repo.save(entity)
        assert saved.id == 1
        assert saved.name == "updated"
        assert saved.status == "completed"

    def test_save_update_not_found_raises(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunRepository()
        entity = BenchmarkRunEntity(
            id=999,
            name="x",
            status="running",
            endpoint_type="LLM_Provider",
        )
        with pytest.raises(ValueError, match="no benchmark_run"):
            repo.save(entity)
