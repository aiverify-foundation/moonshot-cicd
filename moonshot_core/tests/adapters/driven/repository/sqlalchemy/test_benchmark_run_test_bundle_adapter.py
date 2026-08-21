"""Unit tests for SqlAlchemyBenchmarkRunTestBundleRepository."""

from unittest.mock import MagicMock, patch

import pytest
from adapters.driven.repository.sqlalchemy.benchmark_run_test_bundle_adapter import \
    SqlAlchemyBenchmarkRunTestBundleRepository
from adapters.driven.repository.sqlalchemy.llm_provider_models import \
    BenchmarkRunTestBundleModel
from domain.entities.benchmark_run_test_bundle_entity import \
    BenchmarkRunTestBundleEntity


def _make_mock_bundle_model(id=1, run_id=1, test_bundle_id=2, test_id=3):
    m = MagicMock(spec=BenchmarkRunTestBundleModel)
    m.id = id
    m.run_id = run_id
    m.test_bundle_id = test_bundle_id
    m.test_id = test_id
    return m


def _session_ctx(mock_session):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_session)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


@patch(
    "adapters.driven.repository.sqlalchemy.benchmark_run_test_bundle_adapter.SessionManager"
)
class TestSqlAlchemyBenchmarkRunTestBundleRepository:
    """Tests for SqlAlchemyBenchmarkRunTestBundleRepository."""

    def test_get_by_id_not_found(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        assert repo.get_by_id(999) is None

    def test_get_by_id_found(self, mock_sm_class):
        mock_model = _make_mock_bundle_model(
            id=5,
            run_id=1,
            test_bundle_id=2,
            test_id=3,
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        result = repo.get_by_id(5)
        assert result is not None
        assert result.id == 5
        assert result.run_id == 1
        assert result.test_bundle_id == 2
        assert result.test_id == 3

    def test_get_all_by_run_id_empty(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        assert repo.get_all_by_run_id(1) == []

    def test_get_all_by_run_id_returns_entities(self, mock_sm_class):
        mock_model = _make_mock_bundle_model(id=1, run_id=5)
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_model
        ]
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        result = repo.get_all_by_run_id(5)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].run_id == 5

    def test_save_insert_returns_entity_with_id(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.add.side_effect = lambda m: setattr(m, "id", 11)
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        entity = BenchmarkRunTestBundleEntity(
            run_id=1,
            test_bundle_id=2,
            test_id=3,
        )
        saved = repo.save(entity)
        assert saved.id == 11
        assert saved.run_id == 1
        mock_session.add.assert_called_once()

    def test_save_with_id_raises(self, mock_sm_class):
        mock_session = MagicMock()
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        entity = BenchmarkRunTestBundleEntity(
            id=999,
            run_id=1,
            test_bundle_id=2,
            test_id=3,
        )
        with pytest.raises(ValueError, match="Cannot save: entity has id set"):
            repo.save(entity)

    def test_update_returns_entity(self, mock_sm_class):
        mock_model = _make_mock_bundle_model(
            id=1,
            run_id=1,
            test_bundle_id=2,
            test_id=3,
        )
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_model
        )
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        entity = BenchmarkRunTestBundleEntity(
            id=1,
            run_id=1,
            test_bundle_id=2,
            test_id=4,
        )
        result = repo.update(entity)
        assert result.id == 1
        assert result.test_id == 4

    def test_update_not_found_raises(self, mock_sm_class):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_sm_class.get_instance.return_value.get_session.return_value = _session_ctx(
            mock_session
        )
        repo = SqlAlchemyBenchmarkRunTestBundleRepository()
        entity = BenchmarkRunTestBundleEntity(
            id=999,
            run_id=1,
            test_bundle_id=2,
            test_id=3,
        )
        with pytest.raises(ValueError, match="no benchmark_run_test_bundle"):
            repo.update(entity)
