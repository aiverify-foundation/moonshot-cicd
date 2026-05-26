"""Tests for DatabaseModelConfigService (relational llm_provider_model_config writes)."""

from pathlib import Path

import pytest
from datetime import datetime, timezone

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderModel,
    LLMProviderModelModel,
    LLMProviderModelConfigModel,
    LLMProviderEndpointConfigParametersModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.dto.model_config_dto import (
    CreateDatabaseModelConfigBody,
    UpdateDatabaseModelConfigBody,
)
from application.services.database_model_config_service import (
    DatabaseModelConfigBadRequestError,
    DatabaseModelConfigConflictError,
    DatabaseModelConfigNotFoundError,
    DatabaseModelConfigService,
)


@pytest.fixture(scope="function")
def test_db_path():
    moonshot_core_root: Path = (
        Path(__file__).parent.parent.parent.parent  # .../moonshot_core
    )
    db_path: Path = moonshot_core_root / "data" / "database" / "moonshot_pytest.db"
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


@pytest.fixture
def db_model_config_service(test_db_env):
    return DatabaseModelConfigService()


def _seed_provider_with_model(*, system_name: str = "db_cfg_svc") -> int:
    """Returns llm_provider_model.id."""
    sm = SessionManager.get_instance()
    with sm.get_session() as session:
        prov = LLMProviderModel(
            name="Svc Test Provider",
            system_name=system_name,
            version=0,
        )
        session.add(prov)
        session.flush()
        model_row = LLMProviderModelModel(
            llm_provider_id=prov.id,
            name="model-a",
        )
        session.add(model_row)
        session.flush()
        return int(model_row.id)


def _seed_provider_only(*, system_name: str = "db_cfg_by_name") -> int:
    """Returns llm_provider.id (no llm_provider_model rows)."""
    sm = SessionManager.get_instance()
    with sm.get_session() as session:
        prov = LLMProviderModel(
            name="ByName Provider",
            system_name=system_name,
            version=0,
        )
        session.add(prov)
        session.flush()
        return int(prov.id)


class TestDatabaseModelConfigServiceCreate:
    def test_create_persists_config_and_parameters(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        model_id = _seed_provider_with_model()
        body = CreateDatabaseModelConfigBody(
            model_id=model_id,
            name="prod",
            savedConfigPairs={"temperature": "0.5", "top_p": "1"},
        )
        dto, created = db_model_config_service.create(body)
        assert created is True
        assert dto.id.isdigit()
        assert dto.name == "prod"
        assert dto.modelname == "model-a"
        assert dto.providerID == "db_cfg_svc"
        assert dto.savedConfigPairs == {"temperature": "0.5", "top_p": "1"}
        assert dto.lastUpdated is not None

    def test_create_rejects_unknown_model_id(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        _seed_provider_with_model()
        with pytest.raises(DatabaseModelConfigBadRequestError, match="No llm_provider_model"):
            db_model_config_service.create(
                CreateDatabaseModelConfigBody(model_id=999_999, name="x")
            )

    def test_create_updates_when_same_model_id_and_name(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        model_id = _seed_provider_with_model()
        first = CreateDatabaseModelConfigBody(
            model_id=model_id,
            name="dup",
            savedConfigPairs={"temperature": "0.1"},
        )
        dto1, created1 = db_model_config_service.create(first)
        assert created1 is True
        second = CreateDatabaseModelConfigBody(
            model_id=model_id,
            name="dup",
            savedConfigPairs={"temperature": "0.9"},
        )
        dto2, created2 = db_model_config_service.create(second)
        assert created2 is False
        assert dto2.id == dto1.id
        assert dto2.savedConfigPairs == {"temperature": "0.9"}

    def test_create_by_provider_creates_model_row(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        provider_id = _seed_provider_only()
        body = CreateDatabaseModelConfigBody(
            llm_provider_id=provider_id,
            model_name="  gpt-new  ",
            name="cfg-a",
            savedConfigPairs={"temperature": "0.2"},
        )
        dto, _ = db_model_config_service.create(body)
        assert dto.name == "cfg-a"
        assert dto.modelname == "gpt-new"
        assert dto.providerID == "db_cfg_by_name"
        assert dto.savedConfigPairs == {"temperature": "0.2"}

    def test_create_by_provider_reuses_existing_model(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        provider_id = _seed_provider_only(system_name="db_reuse")
        first = CreateDatabaseModelConfigBody(
            llm_provider_id=provider_id,
            model_name="shared-model",
            name="cfg-one",
        )
        dto1, _ = db_model_config_service.create(first)
        second = CreateDatabaseModelConfigBody(
            llm_provider_id=provider_id,
            model_name="shared-model",
            name="cfg-two",
        )
        dto2, _ = db_model_config_service.create(second)
        assert dto1.modelId == dto2.modelId
        assert dto1.modelname == dto2.modelname == "shared-model"

    def test_create_by_provider_rejects_unknown_provider(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        with pytest.raises(DatabaseModelConfigBadRequestError, match="No llm_provider"):
            db_model_config_service.create(
                CreateDatabaseModelConfigBody(
                    llm_provider_id=99_999_999,
                    model_name="m",
                    name="n",
                )
            )


class TestDatabaseModelConfigServiceUpdate:
    def _seed_config(self, *, name: str = "orig") -> tuple[int, int]:
        """Returns (config_id, model_id)."""
        sm = SessionManager.get_instance()
        updated = datetime.now(timezone.utc).replace(tzinfo=None)
        cid: int
        mid: int
        with sm.get_session() as session:
            prov = LLMProviderModel(
                name="Upd Provider",
                system_name="db_cfg_upd",
                version=0,
            )
            session.add(prov)
            session.flush()
            model_row = LLMProviderModelModel(
                llm_provider_id=prov.id,
                name="gpt-upd",
            )
            session.add(model_row)
            session.flush()
            mid = int(model_row.id)
            cfg = LLMProviderModelConfigModel(
                model_id=mid,
                name=name,
                updated_dt=updated,
            )
            session.add(cfg)
            session.flush()
            cid = int(cfg.id)
            session.add(
                LLMProviderEndpointConfigParametersModel(
                    config_id=cid,
                    key="old_key",
                    value="old_val",
                )
            )
        return cid, mid

    def test_update_replaces_fields_and_parameters(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        config_id, model_id = self._seed_config()
        body = UpdateDatabaseModelConfigBody(
            model_id=model_id,
            name="renamed",
            savedConfigPairs={"new_k": "new_v"},
        )
        dto = db_model_config_service.update(config_id, body)
        assert dto.id == str(config_id)
        assert dto.name == "renamed"
        assert dto.savedConfigPairs == {"new_k": "new_v"}
        assert "old_key" not in dto.savedConfigPairs

    def test_update_by_provider_reuses_existing_model(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        config_id, original_model_id = self._seed_config()
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            original_model = (
                session.query(LLMProviderModelModel)
                .filter(LLMProviderModelModel.id == original_model_id)
                .first()
            )
            assert original_model is not None
            provider_id = int(original_model.llm_provider_id)
            reused_model = LLMProviderModelModel(
                llm_provider_id=provider_id,
                name="gpt-reused",
            )
            session.add(reused_model)
            session.flush()
            reused_model_id = int(reused_model.id)

        dto = db_model_config_service.update(
            config_id,
            UpdateDatabaseModelConfigBody(
                llm_provider_id=provider_id,
                model_name="gpt-reused",
                name="renamed",
            ),
        )

        assert dto.id == str(config_id)
        assert dto.modelId == reused_model_id
        assert dto.modelname == "gpt-reused"
        assert dto.name == "renamed"

    def test_update_by_provider_creates_model_row_and_repoints_same_config(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        config_id, original_model_id = self._seed_config()
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            original_model = (
                session.query(LLMProviderModelModel)
                .filter(LLMProviderModelModel.id == original_model_id)
                .first()
            )
            assert original_model is not None
            provider_id = int(original_model.llm_provider_id)

        dto = db_model_config_service.update(
            config_id,
            UpdateDatabaseModelConfigBody(
                llm_provider_id=provider_id,
                model_name="gpt-created-on-update",
                name="renamed",
            ),
        )

        assert dto.id == str(config_id)
        assert dto.modelId != original_model_id
        assert dto.modelname == "gpt-created-on-update"
        assert dto.name == "renamed"

        with sm.get_session() as session:
            created_model = (
                session.query(LLMProviderModelModel)
                .filter(
                    LLMProviderModelModel.llm_provider_id == provider_id,
                    LLMProviderModelModel.name == "gpt-created-on-update",
                )
                .first()
            )
            cfg = (
                session.query(LLMProviderModelConfigModel)
                .filter(LLMProviderModelConfigModel.id == config_id)
                .first()
            )
            assert created_model is not None
            assert cfg is not None
            assert int(created_model.id) == dto.modelId
            assert int(cfg.model_id) == dto.modelId

    def test_update_not_found(self, db_model_config_service: DatabaseModelConfigService):
        _seed_provider_with_model(system_name="other")
        with pytest.raises(DatabaseModelConfigNotFoundError):
            db_model_config_service.update(
                99_999_999,
                UpdateDatabaseModelConfigBody(model_id=1, name="n"),
            )

    def test_update_conflict_second_config_same_name(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            prov = LLMProviderModel(
                name="P",
                system_name="db_two_cfg",
                version=0,
            )
            session.add(prov)
            session.flush()
            m = LLMProviderModelModel(llm_provider_id=prov.id, name="m")
            session.add(m)
            session.flush()
            mid = int(m.id)
            c1 = LLMProviderModelConfigModel(
                model_id=mid,
                name="first",
                updated_dt=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            c2 = LLMProviderModelConfigModel(
                model_id=mid,
                name="second",
                updated_dt=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            session.add(c1)
            session.add(c2)
            session.flush()
            id1, id2 = int(c1.id), int(c2.id)

        with pytest.raises(DatabaseModelConfigConflictError, match="Another config"):
            db_model_config_service.update(
                id2,
                UpdateDatabaseModelConfigBody(model_id=mid, name="first"),
            )

    def test_update_bad_model_id(
        self, db_model_config_service: DatabaseModelConfigService
    ):
        config_id, model_id = self._seed_config()
        with pytest.raises(DatabaseModelConfigBadRequestError, match="No llm_provider_model"):
            db_model_config_service.update(
                config_id,
                UpdateDatabaseModelConfigBody(model_id=999_999_999, name="x"),
            )
