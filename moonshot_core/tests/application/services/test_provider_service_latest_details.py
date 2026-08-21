import base64
import pytest
from datetime import datetime, timezone
from pathlib import Path

from adapters.connector.openai_adapter import OpenAIAdapter
from adapters.connector.together_adapter import TogetherAdapter
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderApiKeyModel,
    LLMProviderModel,
    LLMProviderModelModel,
    LLMProviderEndpointConfigModel,
    LLMProviderModelConfigModel,
    LLMProviderModelConfigParametersModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.provider_service import ProviderService


@pytest.fixture(scope="function")
def test_db_path():
    """Create a temporary database path for testing ProviderService."""
    moonshot_core_root: Path = (
        Path(__file__).parent.parent.parent.parent  # .../moonshot_core
    )
    db_path: Path = moonshot_core_root / "data" / "database" / "moonshot_pytest.db"

    if db_path.exists():
        db_path.unlink()

    yield str(db_path)

    # DB cleanup is intentionally skipped as other tests may rely on it


@pytest.fixture(scope="function")
def test_db_env(test_db_path, monkeypatch):
    """Set up test database environment variable and reset SessionManager."""
    monkeypatch.setenv("MOONSHOT_DB_PATH", test_db_path)
    SessionManager.reset_instance()

    yield

    SessionManager.reset_instance()
    monkeypatch.delenv("MOONSHOT_DB_PATH", raising=False)


@pytest.fixture
def provider_service(test_db_env):
    """Create a ProviderService instance backed by a real SessionManager/DB."""
    return ProviderService()


def _seed_provider_with_models_and_endpoints(system_name: str):
    """Insert provider rows plus associated models and endpoint configs."""
    session_manager = SessionManager.get_instance()
    with session_manager.get_session() as session:
        # two versions, ensure ordering by version desc picks the highest
        older = LLMProviderModel(
            name="Test Provider Old",
            system_name=system_name,
            version=0,
        )
        latest = LLMProviderModel(
            name="Test Provider Latest",
            system_name=system_name,
            version=1,
        )
        session.add(older)
        session.add(latest)
        session.flush()

        model_row = LLMProviderModelModel(
            llm_provider_id=latest.id,
            name="test-model",
        )
        endpoint_row = LLMProviderEndpointConfigModel(
            llm_provider_id=latest.id,
            name="test-endpoint",
        )
        session.add(model_row)
        session.add(endpoint_row)
        session.commit()

        return latest.id


class TestProviderServiceLatestDetails:
    def test_returns_none_when_no_provider(self, provider_service: ProviderService):
        """Service should return None when no provider exists for system_name."""
        details = provider_service.get_latest_provider_details_by_system_name(
            "nonexistent_system_name"
        )
        assert details is None

    def test_returns_latest_version_with_models_and_endpoints(
        self,
        provider_service: ProviderService,
    ):
        """Service should return latest-version provider plus related models and endpoints."""
        system_name = "test_system_name"
        latest_id = _seed_provider_with_models_and_endpoints(system_name)

        details = provider_service.get_latest_provider_details_by_system_name(
            system_name
        )

        assert details is not None
        assert details.provider.system_name == system_name
        assert details.provider.version == 1
        # ensure we picked the latest provider row
        assert str(latest_id) == details.provider.id

        assert len(details.models) == 1
        assert details.models[0].name == "test-model"

        assert len(details.endpoint_configs) == 1
        assert details.endpoint_configs[0].name == "test-endpoint"
        assert details.api_key_configured is False

    def test_latest_details_api_key_configured_true_when_key_row_exists(
        self,
        provider_service: ProviderService,
    ):
        system_name = "test_system_with_api_key"
        latest_id = _seed_provider_with_models_and_endpoints(system_name)
        session_manager = SessionManager.get_instance()
        with session_manager.get_session() as session:
            session.add(
                LLMProviderApiKeyModel(
                    llm_provider_id=latest_id,
                    encrypted_key=base64.b64encode(b"ciphertext").decode("ascii"),
                    salt=base64.b64encode(b"s" * 32).decode("ascii"),
                    nonce=base64.b64encode(b"n" * 12).decode("ascii"),
                    authentication_tag=base64.b64encode(b"t" * 16).decode("ascii"),
                )
            )
            session.commit()

        details = provider_service.get_latest_provider_details_by_system_name(
            system_name
        )
        assert details is not None
        assert details.api_key_configured is True


def _seed_provider_with_db_model_config(
    *,
    provider_name: str = "DB Config Provider",
    system_name: str = "db_cfg_provider",
    model_name: str = "gpt-test",
    config_name: str = "prod",
) -> None:
    """Insert provider, model, llm_provider_model_config, and parameter rows."""
    session_manager = SessionManager.get_instance()
    updated = datetime.now(timezone.utc).replace(tzinfo=None)
    with session_manager.get_session() as session:
        prov = LLMProviderModel(
            name=provider_name,
            system_name=system_name,
            version=0,
        )
        session.add(prov)
        session.flush()
        model_row = LLMProviderModelModel(
            llm_provider_id=prov.id,
            name=model_name,
        )
        session.add(model_row)
        session.flush()
        cfg = LLMProviderModelConfigModel(
            model_id=model_row.id,
            name=config_name,
            updated_dt=updated,
        )
        session.add(cfg)
        session.flush()
        session.add(
            LLMProviderModelConfigParametersModel(
                config_id=cfg.id,
                key="temperature",
                value="0.7",
            )
        )
        session.commit()


class TestProviderServiceDatabaseModelConfigs:
    def test_returns_configs_from_relational_tables_only(
        self,
        provider_service: ProviderService,
    ):
        _seed_provider_with_db_model_config()
        rows = provider_service.list_providers_with_database_model_configs()
        match = [r for r in rows if r.providerName == "DB Config Provider"]
        assert len(match) == 1
        item = match[0]
        assert len(item.configs) == 1
        cfg = item.configs[0]
        assert cfg.name == "prod"
        assert cfg.modelname == "gpt-test"
        assert cfg.providerID == "db_cfg_provider"
        assert cfg.savedConfigPairs == {"temperature": "0.7"}
        assert cfg.lastUpdated is not None
        assert cfg.modelId > 0

    def test_latest_details_includes_database_model_configs(
        self,
        provider_service: ProviderService,
    ):
        _seed_provider_with_db_model_config()
        details = provider_service.get_latest_provider_details_by_system_name(
            "db_cfg_provider"
        )
        assert details is not None
        assert len(details.database_model_configs) == 1
        dmc = details.database_model_configs[0]
        assert dmc.name == "prod"
        assert dmc.modelname == "gpt-test"
        assert dmc.modelId > 0
        assert details.api_key_configured is False

    def test_provider_without_models_has_empty_configs(
        self,
        provider_service: ProviderService,
    ):
        session_manager = SessionManager.get_instance()
        with session_manager.get_session() as session:
            session.add(
                LLMProviderModel(
                    name="No Models Inc",
                    system_name="no_models",
                    version=0,
                )
            )
        rows = provider_service.list_providers_with_database_model_configs()
        match = [r for r in rows if r.providerName == "No Models Inc"]
        assert len(match) == 1
        assert match[0].configs == []

    def test_provider_with_models_but_no_configs_has_empty_configs(
        self,
        provider_service: ProviderService,
    ):
        session_manager = SessionManager.get_instance()
        with session_manager.get_session() as session:
            prov = LLMProviderModel(
                name="Has Model Only",
                system_name="model_only",
                version=0,
            )
            session.add(prov)
            session.flush()
            session.add(
                LLMProviderModelModel(
                    llm_provider_id=prov.id,
                    name="orphan-model",
                )
            )
        rows = provider_service.list_providers_with_database_model_configs()
        match = [r for r in rows if r.providerName == "Has Model Only"]
        assert len(match) == 1
        assert match[0].configs == []


class TestProviderServiceAdapterDefaults:
    def test_list_providers_enriches_known_adapter_defaults(
        self, provider_service: ProviderService
    ):
        session_manager = SessionManager.get_instance()
        with session_manager.get_session() as session:
            session.add(
                LLMProviderModel(
                    name="OpenAI",
                    system_name=OpenAIAdapter.SYSTEM_NAME,
                    version=1,
                )
            )
            session.add(
                LLMProviderModel(
                    name="Together",
                    system_name=TogetherAdapter.SYSTEM_NAME,
                    version=1,
                )
            )
            session.commit()

        rows = provider_service.list_providers()
        by_sys = {p.system_name: p for p in rows}

        oa = by_sys[OpenAIAdapter.SYSTEM_NAME]
        assert oa.defaultConfigPairs == OpenAIAdapter.DEFAULT_CONFIG_PAIRS
        assert oa.defaultModel == OpenAIAdapter.DEFAULT_MODEL
        assert oa.modelTextboxExplanation == OpenAIAdapter.MODEL_TEXTBOX_EXPLANATION

        ta = by_sys[TogetherAdapter.SYSTEM_NAME]
        assert ta.defaultConfigPairs == TogetherAdapter.DEFAULT_CONFIG_PAIRS
        assert ta.defaultModel == TogetherAdapter.DEFAULT_MODEL

    def test_list_providers_unknown_adapter_leaves_empty(
        self, provider_service: ProviderService
    ):
        session_manager = SessionManager.get_instance()
        with session_manager.get_session() as session:
            session.add(
                LLMProviderModel(
                    name="No Connector",
                    system_name="unknown_custom_provider",
                    version=0,
                )
            )
            session.commit()

        rows = provider_service.list_providers()
        assert len(rows) == 1
        p = rows[0]
        assert p.defaultConfigPairs == {}
        assert p.defaultModel == ""

    def test_latest_details_enriches_openai_adapter_defaults(
        self,
        provider_service: ProviderService,
    ):
        session_manager = SessionManager.get_instance()
        with session_manager.get_session() as session:
            session.add(
                LLMProviderModel(
                    name="OpenAI",
                    system_name=OpenAIAdapter.SYSTEM_NAME,
                    version=1,
                )
            )
            session.commit()

        details = provider_service.get_latest_provider_details_by_system_name(
            OpenAIAdapter.SYSTEM_NAME
        )
        assert details is not None
        assert details.provider.defaultConfigPairs == OpenAIAdapter.DEFAULT_CONFIG_PAIRS
        assert details.provider.defaultModel == OpenAIAdapter.DEFAULT_MODEL

