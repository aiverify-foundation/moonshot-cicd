"""Unit tests for BenchmarkRunService."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    CustomAppConfigModel,
    CustomAppModel,
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.benchmark_run_service import BenchmarkRunService
from domain.entities.benchmark_run_entity import BenchmarkRunEntity


@pytest.fixture
def service():
    return BenchmarkRunService()


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root = Path(__file__).resolve().parent.parent.parent.parent
    db_path = moonshot_core_root / "data" / "database" / "moonshot_pytest_benchmark_run_service.db"
    if db_path.exists():
        db_path.unlink()
    yield str(db_path)


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


class TestGetAllRuns:
    """Tests for get_all_runs."""

    @patch(
        "application.services.benchmark_run_service.SqlAlchemyBenchmarkRunRepository"
    )
    def test_returns_empty_when_no_runs(self, mock_repo_class, service):
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = []
        mock_repo_class.return_value = mock_repo

        result = service.get_all_runs()

        assert result == []
        mock_repo.get_all.assert_called_once()

    @patch(
        "application.services.benchmark_run_service.SqlAlchemyBenchmarkRunRepository"
    )
    def test_returns_all_entities(self, mock_repo_class, service):
        t = datetime.now(timezone.utc)
        runs = [
            BenchmarkRunEntity(
                id=1,
                name="run-a",
                status="running",
                endpoint_type="LLM_Provider",
                start_time=t,
            ),
            BenchmarkRunEntity(
                id=2,
                name="run-b",
                status="completed",
                endpoint_type="LLM_Provider",
                start_time=t,
                end_time=t,
            ),
        ]
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = runs
        mock_repo_class.return_value = mock_repo

        result = service.get_all_runs()

        assert result == runs
        mock_repo.get_all.assert_called_once()


class TestToResponseDto:
    def test_includes_endpoint_config_name(self, service):
        entity = BenchmarkRunEntity(
            id=1,
            name="run-a",
            status="completed",
            endpoint_type="LLM_Provider",
            llm_provider_model_config_id=10,
        )
        with patch.object(
            BenchmarkRunService,
            "resolve_endpoint_config_name",
            return_value="Prod",
        ):
            dto = service.to_response_dto(entity)
        assert dto.endpoint_config_name == "Prod"
        assert dto.name == "run-a"


class TestResolveEndpointConfigName:
    def test_returns_model_config_name(self, service, test_db_env):
        updated = datetime.now(timezone.utc).replace(tzinfo=None)
        with SessionManager.get_instance().get_session() as session:
            prov = LLMProviderModel(name="P", system_name="p", version=0)
            session.add(prov)
            session.flush()
            model = LLMProviderModelModel(llm_provider_id=prov.id, name="m")
            session.add(model)
            session.flush()
            cfg = LLMProviderModelConfigModel(
                model_id=model.id,
                name="My Model Config",
                updated_dt=updated,
            )
            session.add(cfg)
            session.flush()
            config_id = cfg.id

        entity = BenchmarkRunEntity(
            id=1,
            name="run",
            status="running",
            endpoint_type="LLM_Provider",
            llm_provider_model_config_id=config_id,
        )
        assert service.resolve_endpoint_config_name(entity) == "My Model Config"

    def test_returns_custom_app_config_name(self, service, test_db_env):
        with SessionManager.get_instance().get_session() as session:
            app = CustomAppModel(name="My App")
            session.add(app)
            session.flush()
            cfg = CustomAppConfigModel(custom_app_id=app.id, name="App Prod")
            session.add(cfg)
            session.flush()
            config_id = cfg.id

        entity = BenchmarkRunEntity(
            id=1,
            name="run",
            status="running",
            endpoint_type="Custom_App",
            custom_app_config_id=config_id,
        )
        assert service.resolve_endpoint_config_name(entity) == "App Prod"

    def test_returns_none_when_no_config_fks(self, service, test_db_env):
        entity = BenchmarkRunEntity(
            id=1,
            name="run",
            status="running",
            endpoint_type="LLM_Provider",
        )
        assert service.resolve_endpoint_config_name(entity) is None
