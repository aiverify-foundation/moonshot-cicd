"""Unit tests for SqlAlchemyBenchmarkRunTestErrorRepository."""

from unittest.mock import MagicMock, patch

import pytest
from adapters.driven.repository.sqlalchemy.benchmark_run_test_error_adapter import (
    SqlAlchemyBenchmarkRunTestErrorRepository,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    BenchmarkRunTestErrorModel,
)
from domain.entities.benchmark_run_test_error_entity import (
    BenchmarkRunTestErrorEntity,
)


@patch(
    "adapters.driven.repository.sqlalchemy.benchmark_run_test_error_adapter.SessionManager"
)
class TestSqlAlchemyBenchmarkRunTestErrorRepository:
    def test_save_insert_returns_entity_with_id(self, mock_sm_class):
        mock_session = MagicMock()

        def set_id_on_add(model):
            model.id = 99

        mock_session.add.side_effect = set_id_on_add
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_session)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestErrorRepository()
        entity = BenchmarkRunTestErrorEntity(
            benchmark_run_test_prompt_id=5,
            error_message="connector timeout",
            error_source="connector",
        )
        saved = repo.save(entity)

        assert saved.id == 99
        assert saved.benchmark_run_test_prompt_id == 5
        assert saved.error_message == "connector timeout"
        assert saved.error_source == "connector"
        mock_session.add.assert_called_once()
        added = mock_session.add.call_args[0][0]
        assert isinstance(added, BenchmarkRunTestErrorModel)
        mock_session.flush.assert_called_once()

    def test_save_with_id_raises(self, mock_sm_class):
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=MagicMock())
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_sm_class.get_instance.return_value.get_session.return_value = mock_cm

        repo = SqlAlchemyBenchmarkRunTestErrorRepository()
        entity = BenchmarkRunTestErrorEntity(
            id=1,
            benchmark_run_test_prompt_id=5,
            error_message="err",
            error_source="metric",
        )
        with pytest.raises(ValueError, match="Cannot save: entity has id set"):
            repo.save(entity)
