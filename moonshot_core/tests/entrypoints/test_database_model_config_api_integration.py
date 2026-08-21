"""
API integration tests: database model configs do not interfere when edited.

Uses the real FastAPI app (entrypoints.api) and relational DB — no service mocks.
Covers create/update via POST/PUT /api/database-model-configs and verification via
GET /api/providers/with-database-model-configs and latest-details.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

MOONSHOT_CORE_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = MOONSHOT_CORE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from adapters.driven.repository.sqlalchemy.llm_provider_models import (  # noqa: E402
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager  # noqa: E402
from application.services.database_model_config_service import (  # noqa: E402
    DatabaseModelConfigService,
)
from application.services.provider_service import ProviderService  # noqa: E402


@pytest.fixture(scope="function")
def test_db_path():
    db_path = MOONSHOT_CORE_ROOT / "data" / "database" / "moonshot_pytest_db_model_config_api.db"
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
def api_client(test_db_env) -> TestClient:
    """TestClient wired to services that use the isolated per-test database."""
    import entrypoints.api as api_module
    from fastapi.testclient import TestClient as _TestClient

    api_module.database_model_config_service = DatabaseModelConfigService()
    api_module.provider_service = ProviderService()
    return _TestClient(api_module.app)


def _seed_provider(*, system_name: str | None = None) -> tuple[int, str]:
    """Insert one llm_provider row; return (provider_id, system_name)."""
    system_name = system_name or f"cfg_iso_{uuid.uuid4().hex[:12]}"
    sm = SessionManager.get_instance()
    with sm.get_session() as session:
        prov = LLMProviderModel(
            name="Isolation Test Provider",
            system_name=system_name,
            version=0,
        )
        session.add(prov)
        session.flush()
        return int(prov.id), system_name


def _api_create(
    client: TestClient,
    *,
    llm_provider_id: int,
    model_name: str,
    name: str,
    saved_config_pairs: dict[str, str] | None = None,
) -> dict:
    response = client.post(
        "/api/database-model-configs",
        json={
            "llm_provider_id": llm_provider_id,
            "model_name": model_name,
            "name": name,
            "savedConfigPairs": saved_config_pairs or {},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _api_update(
    client: TestClient,
    config_id: int,
    *,
    llm_provider_id: int,
    model_name: str,
    name: str,
    saved_config_pairs: dict[str, str] | None = None,
) -> dict:
    response = client.put(
        f"/api/database-model-configs/{config_id}",
        json={
            "llm_provider_id": llm_provider_id,
            "model_name": model_name,
            "name": name,
            "savedConfigPairs": saved_config_pairs or {},
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _config_from_latest_details(
    client: TestClient, system_name: str, config_id: str
) -> dict | None:
    response = client.get(f"/api/providers/by-system-name/{system_name}/latest-details")
    assert response.status_code == 200, response.text
    configs = response.json().get("database_model_configs") or []
    for cfg in configs:
        if str(cfg.get("id")) == str(config_id):
            return cfg
    return None


def _configs_for_provider(client: TestClient, provider_name: str) -> list[dict]:
    response = client.get("/api/providers/with-database-model-configs")
    assert response.status_code == 200, response.text
    for row in response.json():
        if row.get("providerName") == provider_name:
            return list(row.get("configs") or [])
    return []


def _create_two_configs_same_model_name(
    client: TestClient, provider_id: int
) -> tuple[dict, dict]:
    cfg_a = _api_create(
        client,
        llm_provider_id=provider_id,
        model_name="gpt-4",
        name="Prod A",
        saved_config_pairs={"temperature": "0.1"},
    )
    cfg_b = _api_create(
        client,
        llm_provider_id=provider_id,
        model_name="gpt-4",
        name="Prod B",
        saved_config_pairs={"temperature": "0.9"},
    )
    return cfg_a, cfg_b


class TestDatabaseModelConfigApiIsolation:
    def test_create_same_model_name_yields_separate_model_rows(
        self, api_client: TestClient
    ):
        provider_id, _ = _seed_provider()
        cfg_a, cfg_b = _create_two_configs_same_model_name(api_client, provider_id)

        assert cfg_a["id"] != cfg_b["id"]
        assert cfg_a["modelId"] != cfg_b["modelId"]
        assert cfg_a["modelname"] == cfg_b["modelname"] == "gpt-4"

    def test_edit_model_name_on_one_config_does_not_change_the_other(
        self, api_client: TestClient
    ):
        provider_id, system_name = _seed_provider()
        cfg_a, cfg_b = _create_two_configs_same_model_name(api_client, provider_id)
        model_id_a = cfg_a["modelId"]
        model_id_b = cfg_b["modelId"]

        updated_a = _api_update(
            api_client,
            int(cfg_a["id"]),
            llm_provider_id=provider_id,
            model_name="gpt-4.1",
            name="Prod A",
            saved_config_pairs={"temperature": "0.1"},
        )

        assert updated_a["modelId"] == model_id_a
        assert updated_a["modelname"] == "gpt-4.1"

        b_after = _config_from_latest_details(api_client, system_name, cfg_b["id"])
        assert b_after is not None
        assert b_after["modelId"] == model_id_b
        assert b_after["modelname"] == "gpt-4"
        assert b_after["savedConfigPairs"] == {"temperature": "0.9"}

    def test_edit_to_existing_model_name_string_does_not_repoint_to_other_row(
        self, api_client: TestClient
    ):
        provider_id, system_name = _seed_provider()
        cfg_a, cfg_b = _create_two_configs_same_model_name(api_client, provider_id)
        model_id_a = cfg_a["modelId"]
        model_id_b = cfg_b["modelId"]

        _api_update(
            api_client,
            int(cfg_b["id"]),
            llm_provider_id=provider_id,
            model_name="gpt-4.1",
            name="Prod B",
            saved_config_pairs={"temperature": "0.9"},
        )

        updated_a = _api_update(
            api_client,
            int(cfg_a["id"]),
            llm_provider_id=provider_id,
            model_name="gpt-4.1",
            name="Prod A",
            saved_config_pairs={"temperature": "0.1"},
        )

        assert updated_a["modelId"] == model_id_a
        assert updated_a["modelId"] != model_id_b
        assert updated_a["modelname"] == "gpt-4.1"

        b_after = _config_from_latest_details(api_client, system_name, cfg_b["id"])
        assert b_after is not None
        assert b_after["modelId"] == model_id_b
        assert b_after["modelname"] == "gpt-4.1"

    def test_edit_config_label_on_one_config_does_not_rename_the_other(
        self, api_client: TestClient
    ):
        provider_id, system_name = _seed_provider()
        cfg_a, cfg_b = _create_two_configs_same_model_name(api_client, provider_id)

        _api_update(
            api_client,
            int(cfg_a["id"]),
            llm_provider_id=provider_id,
            model_name="gpt-4",
            name="Prod A v2",
            saved_config_pairs={"temperature": "0.1"},
        )

        b_after = _config_from_latest_details(api_client, system_name, cfg_b["id"])
        assert b_after is not None
        assert b_after["name"] == "Prod B"

    def test_edit_parameters_on_one_config_does_not_change_the_other(
        self, api_client: TestClient
    ):
        provider_id, system_name = _seed_provider()
        cfg_a, cfg_b = _create_two_configs_same_model_name(api_client, provider_id)

        _api_update(
            api_client,
            int(cfg_a["id"]),
            llm_provider_id=provider_id,
            model_name="gpt-4",
            name="Prod A",
            saved_config_pairs={"temperature": "0.3", "top_p": "0.8"},
        )

        b_after = _config_from_latest_details(api_client, system_name, cfg_b["id"])
        assert b_after is not None
        assert b_after["savedConfigPairs"] == {"temperature": "0.9"}

    def test_update_rejects_foreign_model_id(self, api_client: TestClient):
        provider_id, _ = _seed_provider()
        cfg_a, cfg_b = _create_two_configs_same_model_name(api_client, provider_id)

        response = api_client.put(
            f"/api/database-model-configs/{cfg_a['id']}",
            json={
                "model_id": cfg_b["modelId"],
                "name": "Prod A",
                "savedConfigPairs": {"temperature": "0.1"},
            },
        )
        assert response.status_code == 400
        assert "does not match" in response.json()["detail"]

        a_after = _api_update(
            api_client,
            int(cfg_a["id"]),
            llm_provider_id=provider_id,
            model_name="gpt-4",
            name="Prod A",
            saved_config_pairs={"temperature": "0.1"},
        )
        assert a_after["modelId"] == cfg_a["modelId"]

    def test_list_providers_reflects_independent_configs_after_edits(
        self, api_client: TestClient
    ):
        provider_id, _ = _seed_provider(system_name="cfg_iso_list")
        cfg_a, cfg_b = _create_two_configs_same_model_name(api_client, provider_id)

        _api_update(
            api_client,
            int(cfg_a["id"]),
            llm_provider_id=provider_id,
            model_name="gpt-4.1",
            name="Prod A renamed",
            saved_config_pairs={"temperature": "0.5"},
        )

        listed = _configs_for_provider(api_client, "Isolation Test Provider")
        by_id = {str(c["id"]): c for c in listed}

        assert by_id[cfg_a["id"]]["modelname"] == "gpt-4.1"
        assert by_id[cfg_a["id"]]["name"] == "Prod A renamed"
        assert by_id[cfg_a["id"]]["savedConfigPairs"] == {"temperature": "0.5"}

        assert by_id[cfg_b["id"]]["modelname"] == "gpt-4"
        assert by_id[cfg_b["id"]]["name"] == "Prod B"
        assert by_id[cfg_b["id"]]["savedConfigPairs"] == {"temperature": "0.9"}
        assert by_id[cfg_a["id"]]["modelId"] != by_id[cfg_b["id"]]["modelId"]

    def test_create_never_upserts_existing_config_with_same_name_on_shared_model_row(
        self, api_client: TestClient
    ):
        """When model_id is supplied explicitly, duplicate (model_id, config name) is rejected."""
        provider_id, _ = _seed_provider()
        sm = SessionManager.get_instance()
        with sm.get_session() as session:
            model_row = LLMProviderModelModel(
                llm_provider_id=provider_id,
                name="shared-row",
            )
            session.add(model_row)
            session.flush()
            model_id = int(model_row.id)

        first = api_client.post(
            "/api/database-model-configs",
            json={"model_id": model_id, "name": "dup", "savedConfigPairs": {"k": "1"}},
        )
        assert first.status_code == 201

        second = api_client.post(
            "/api/database-model-configs",
            json={"model_id": model_id, "name": "dup", "savedConfigPairs": {"k": "2"}},
        )
        assert second.status_code == 409

        with sm.get_session() as session:
            rows = (
                session.query(LLMProviderModelConfigModel)
                .filter(LLMProviderModelConfigModel.model_id == model_id)
                .all()
            )
            assert len(rows) == 1
            assert rows[0].name == "dup"
