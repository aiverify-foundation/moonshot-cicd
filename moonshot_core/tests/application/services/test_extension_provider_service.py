"""
Extension providers: ``providers.json`` in the benchmark-extensions overlay.

Covers reading and validating the file, the system_name to adapter-module fallback, the
default-value enrichment, and hiding extension providers when the overlay is not active.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adapters.driven.repository.sqlalchemy.llm_provider_adapter import LLMProviderAdapter
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelConfigParametersModel,
    LLMProviderModelModel,
)
from adapters.driven.repository.sqlalchemy.moonshot_config_adapter import MoonshotConfigAdapter
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.database_connector_config_service import (
    DatabaseConnectorConfigError,
    DatabaseConnectorConfigService,
)
from application.services.extension_provider_service import (
    EXTENSION_PROVIDER_SYSTEM_NAMES_KEY,
    ExtensionProviderService,
)
from application.services.provider_seed_service import ProviderSeedService
from application.services.provider_service import ProviderService
from domain.services import benchmark_extensions as be
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.feature_flags import FeatureFlags

MOONSHOT_CORE_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_EXTENSIONS_DIR = MOONSHOT_CORE_ROOT / "benchmark-extensions.example"

EXT_SYSTEM_NAME = "ext_test_provider"


def _patch_moon807(enabled: bool):
    adapter = MagicMock()
    adapter.load_flags.return_value = {FeatureFlagNames.AIVET_OCT2026_MOON807: enabled}
    return patch(
        "domain.services.feature_flags.FeatureFlagAdapterFactory.get_adapter",
        return_value=adapter,
    )


def _entry(**overrides) -> dict:
    entry = {
        "name": "Ext Test Provider",
        "system_name": EXT_SYSTEM_NAME,
        "version": 1,
        "adapter_module": "ext_test_adapter",
        "defaultModel": "ext-model",
        "modelTextboxExplanation": "Enter an ext model",
        "defaultConfigPairs": {"temperature": "0.5"},
    }
    entry.update(overrides)
    return entry


@pytest.fixture(autouse=True)
def moon807_enabled():
    FeatureFlags.reset()
    be.reset_invalid_extensions()
    ExtensionProviderService.reset()
    with _patch_moon807(True):
        yield
    FeatureFlags.reset()
    be.reset_invalid_extensions()
    ExtensionProviderService.reset()


@pytest.fixture
def ext_root(tmp_path, monkeypatch) -> Path:
    """An extensions directory that the app resolves as the active overlay."""
    root = tmp_path / "ext"
    (root / "adapters" / "connector").mkdir(parents=True)
    monkeypatch.setenv(be.BENCHMARK_EXTENSIONS_DIR_ENV, str(root))
    return root


def _write_providers(root: Path, content) -> Path:
    path = root / "adapters" / "connector" / "providers.json"
    path.write_text(content if isinstance(content, str) else json.dumps(content))
    ExtensionProviderService.reset()
    return path


@pytest.fixture
def test_db_env(tmp_path, monkeypatch):
    monkeypatch.setenv("MOONSHOT_DB_PATH", str(tmp_path / "moonshot_ext_providers.db"))
    SessionManager.reset_instance()
    yield
    SessionManager.reset_instance()


# ------------------------------------------------------------------ reading the file


def test_no_overlay_returns_nothing(monkeypatch):
    monkeypatch.delenv(be.BENCHMARK_EXTENSIONS_DIR_ENV, raising=False)
    # Make sure the Docker volume path does not exist for this check.
    with patch.object(be, "DOCKER_DATA_DIR", Path("/nonexistent-moonshot-dir")):
        assert ExtensionProviderService().load_definitions() == []


def test_flag_off_returns_nothing(ext_root):
    _write_providers(ext_root, {"providers": [_entry()]})
    with _patch_moon807(False):
        FeatureFlags.reset()
        assert ExtensionProviderService().load_definitions() == []


def test_missing_file_returns_nothing(ext_root):
    assert ExtensionProviderService().load_definitions() == []


def test_valid_file_is_loaded(ext_root):
    _write_providers(ext_root, {"providers": [_entry()]})
    service = ExtensionProviderService()

    definitions = service.load_definitions()

    assert definitions == [_entry()]
    assert service.get_adapter_module(EXT_SYSTEM_NAME) == "ext_test_adapter"
    assert service.get_adapter_module("unknown") is None


def test_seed_definitions_have_only_seed_keys(ext_root):
    _write_providers(ext_root, {"providers": [_entry()]})

    seed = ExtensionProviderService().load_seed_definitions()

    assert seed == [
        {
            "name": "Ext Test Provider",
            "system_name": EXT_SYSTEM_NAME,
            "version": 1,
            "defaultModel": "ext-model",
            "modelTextboxExplanation": "Enter an ext model",
            "defaultConfigPairs": {"temperature": "0.5"},
        }
    ]


def test_optional_fields_default(ext_root):
    _write_providers(
        ext_root,
        {"providers": [{"name": "N", "system_name": "s", "version": 0, "adapter_module": "m"}]},
    )

    (definition,) = ExtensionProviderService().load_definitions()

    assert definition["defaultModel"] == ""
    assert definition["modelTextboxExplanation"] == ""
    assert definition["defaultConfigPairs"] == {}


def test_default_config_pair_values_become_strings(ext_root):
    _write_providers(ext_root, {"providers": [_entry(defaultConfigPairs={"temperature": 1.0})]})

    (definition,) = ExtensionProviderService().load_definitions()

    assert definition["defaultConfigPairs"] == {"temperature": "1.0"}


def test_malformed_json_returns_nothing(ext_root):
    _write_providers(ext_root, "{ not json")
    assert ExtensionProviderService().load_definitions() == []


@pytest.mark.parametrize("content", [[], {"providers": "nope"}, {"other": []}, "null"])
def test_wrong_top_level_shape_returns_nothing(ext_root, content):
    _write_providers(ext_root, content)
    assert ExtensionProviderService().load_definitions() == []


@pytest.mark.parametrize(
    "bad",
    [
        "not an object",
        _entry(name=""),
        _entry(system_name=None),
        _entry(adapter_module=3),
        _entry(version="1"),
        _entry(version=True),
        _entry(adapter_module="../escape"),
        _entry(adapter_module="a.b"),
        _entry(defaultModel=5),
        _entry(defaultConfigPairs=["x"]),
        _entry(system_name="openai_adapter"),
        _entry(system_name="together_ai"),
        _entry(system_name="aws_bedrock_adapter"),
    ],
)
def test_invalid_entry_is_skipped_and_valid_one_kept(ext_root, bad):
    good = _entry(system_name="good_provider", adapter_module="good_adapter")
    _write_providers(ext_root, {"providers": [bad, good]})

    definitions = ExtensionProviderService().load_definitions()

    assert [d["system_name"] for d in definitions] == ["good_provider"]


def test_duplicate_system_name_in_file_keeps_first(ext_root):
    _write_providers(
        ext_root,
        {"providers": [_entry(version=1), _entry(version=2, adapter_module="other_adapter")]},
    )

    definitions = ExtensionProviderService().load_definitions()

    assert len(definitions) == 1
    assert definitions[0]["version"] == 1


def test_invalid_overlay_returns_nothing(ext_root):
    _write_providers(ext_root, {"providers": [_entry()]})
    assert ExtensionProviderService().load_definitions()

    be.mark_extensions_invalid(ext_root, "test reason", reload_app_config=False)

    assert ExtensionProviderService().load_definitions() == []


def test_definitions_are_cached_until_reset(ext_root):
    path = _write_providers(ext_root, {"providers": [_entry()]})
    service = ExtensionProviderService()
    assert len(service.load_definitions()) == 1

    path.write_text(json.dumps({"providers": []}))
    assert len(service.load_definitions()) == 1  # still the cached read

    ExtensionProviderService.reset()
    assert service.load_definitions() == []


def test_example_providers_json_is_valid(monkeypatch):
    monkeypatch.setenv(be.BENCHMARK_EXTENSIONS_DIR_ENV, str(EXAMPLE_EXTENSIONS_DIR))

    definitions = ExtensionProviderService().load_definitions()

    assert [d["system_name"] for d in definitions] == ["benchmark_extension_openai_adapter"]
    assert definitions[0]["adapter_module"] == "benchmark_extension_openai_adapter"


# ------------------------------------------------------------------ seeding and recording


def test_seed_adds_extension_provider_and_records_it(ext_root, test_db_env):
    _write_providers(ext_root, {"providers": [_entry()]})

    ProviderSeedService(provider_repository=LLMProviderAdapter()).seed_hardcoded_providers()

    rows = [p for p in LLMProviderAdapter().list_providers() if p.system_name == EXT_SYSTEM_NAME]
    assert len(rows) == 1
    assert rows[0].name == "Ext Test Provider"
    assert rows[0].version == 1
    recorded = MoonshotConfigAdapter().get_by_key(EXTENSION_PROVIDER_SYSTEM_NAMES_KEY)
    assert json.loads(recorded.value) == [EXT_SYSTEM_NAME]


def test_seed_without_overlay_records_nothing(monkeypatch, test_db_env):
    monkeypatch.delenv(be.BENCHMARK_EXTENSIONS_DIR_ENV, raising=False)

    with patch.object(be, "DOCKER_DATA_DIR", Path("/nonexistent-moonshot-dir")):
        ProviderSeedService(provider_repository=LLMProviderAdapter()).seed_hardcoded_providers()

    assert MoonshotConfigAdapter().get_by_key(EXTENSION_PROVIDER_SYSTEM_NAMES_KEY) is None


def test_recorded_names_only_grow(test_db_env):
    service = ExtensionProviderService()

    service.record_seeded_system_names(["a"])
    service.record_seeded_system_names(["b"])
    service.record_seeded_system_names([])
    service.record_seeded_system_names(["a"])

    recorded = MoonshotConfigAdapter().get_by_key(EXTENSION_PROVIDER_SYSTEM_NAMES_KEY)
    assert json.loads(recorded.value) == ["a", "b"]


# ------------------------------------------------------------------ portal enrichment


def _add_provider(system_name: str = EXT_SYSTEM_NAME, version: int = 1) -> None:
    with SessionManager.get_instance().get_session() as session:
        session.add(LLMProviderModel(name="Ext Test Provider", system_name=system_name, version=version))


def test_list_providers_uses_extension_defaults(ext_root, test_db_env):
    _write_providers(ext_root, {"providers": [_entry()]})
    ProviderSeedService(provider_repository=LLMProviderAdapter()).seed_hardcoded_providers()

    rows = ProviderService().list_providers()

    (ext,) = [p for p in rows if p.system_name == EXT_SYSTEM_NAME]
    assert ext.defaultModel == "ext-model"
    assert ext.modelTextboxExplanation == "Enter an ext model"
    assert ext.defaultConfigPairs == {"temperature": "0.5"}


# ------------------------------------------------------------------ visibility


def _visible_in_all_portal_paths(service: ProviderService) -> dict[str, bool]:
    listed = any(p.system_name == EXT_SYSTEM_NAME for p in service.list_providers())
    details = service.get_latest_provider_details_by_system_name(EXT_SYSTEM_NAME) is not None
    with_configs = any(
        r.providerName == "Ext Test Provider" for r in service.list_providers_with_database_model_configs()
    )
    return {"list": listed, "details": details, "configs": with_configs}


def _seed_extension_provider(ext_root: Path) -> None:
    _write_providers(ext_root, {"providers": [_entry()]})
    ProviderSeedService(provider_repository=LLMProviderAdapter()).seed_hardcoded_providers()


def test_extension_provider_visible_while_overlay_active(ext_root, test_db_env):
    _seed_extension_provider(ext_root)

    assert _visible_in_all_portal_paths(ProviderService()) == {"list": True, "details": True, "configs": True}


def test_extension_provider_hidden_when_flag_off(ext_root, test_db_env):
    _seed_extension_provider(ext_root)

    with _patch_moon807(False):
        FeatureFlags.reset()
        assert _visible_in_all_portal_paths(ProviderService()) == {
            "list": False,
            "details": False,
            "configs": False,
        }


def test_extension_provider_hidden_when_directory_unset(ext_root, test_db_env, monkeypatch):
    _seed_extension_provider(ext_root)

    monkeypatch.delenv(be.BENCHMARK_EXTENSIONS_DIR_ENV)
    with patch.object(be, "DOCKER_DATA_DIR", Path("/nonexistent-moonshot-dir")):
        assert _visible_in_all_portal_paths(ProviderService()) == {
            "list": False,
            "details": False,
            "configs": False,
        }


def test_extension_provider_hidden_when_overlay_invalid(ext_root, test_db_env):
    _seed_extension_provider(ext_root)

    be.mark_extensions_invalid(ext_root, "test reason", reload_app_config=False)

    assert _visible_in_all_portal_paths(ProviderService()) == {"list": False, "details": False, "configs": False}


def test_extension_provider_hidden_when_removed_from_json(ext_root, test_db_env):
    _seed_extension_provider(ext_root)

    _write_providers(ext_root, {"providers": []})

    assert _visible_in_all_portal_paths(ProviderService()) == {"list": False, "details": False, "configs": False}


def test_extension_provider_visible_again_when_overlay_returns(ext_root, test_db_env):
    _seed_extension_provider(ext_root)
    _write_providers(ext_root, {"providers": []})
    assert _visible_in_all_portal_paths(ProviderService())["list"] is False

    _write_providers(ext_root, {"providers": [_entry()]})

    assert _visible_in_all_portal_paths(ProviderService()) == {"list": True, "details": True, "configs": True}


def test_unrecorded_providers_stay_visible(test_db_env):
    _add_provider(system_name="some_other_system_name")
    service = ProviderService()

    assert any(p.system_name == "some_other_system_name" for p in service.list_providers())
    assert service.get_latest_provider_details_by_system_name("some_other_system_name") is not None


# ------------------------------------------------------------------ adapter mapping fallback


def _add_provider_with_config(system_name: str) -> tuple[int, int, int]:
    with SessionManager.get_instance().get_session() as session:
        provider = LLMProviderModel(name="Mapped", system_name=system_name, version=1)
        session.add(provider)
        session.flush()
        model = LLMProviderModelModel(llm_provider_id=provider.id, name="m")
        session.add(model)
        session.flush()
        cfg = LLMProviderModelConfigModel(model_id=model.id, name="cfg")
        session.add(cfg)
        session.flush()
        session.add(LLMProviderModelConfigParametersModel(config_id=cfg.id, key="temperature", value="0.2"))
        return provider.id, model.id, cfg.id


def test_connector_entity_resolves_extension_adapter_module(monkeypatch, test_db_env):
    monkeypatch.chdir(MOONSHOT_CORE_ROOT)
    monkeypatch.setenv(be.BENCHMARK_EXTENSIONS_DIR_ENV, str(EXAMPLE_EXTENSIONS_DIR))
    provider_id, model_id, cfg_id = _add_provider_with_config("benchmark_extension_openai_adapter")

    entity = DatabaseConnectorConfigService().build_connector_entity(
        llm_provider_id=provider_id,
        llm_provider_model_id=model_id,
        llm_provider_model_config_id=cfg_id,
    )

    assert entity.connector_adapter == "benchmark_extension_openai_adapter"
    assert entity.model == "m"
    assert entity.params["temperature"] == "0.2"


def test_connector_entity_fails_for_extension_provider_without_overlay(monkeypatch, test_db_env):
    monkeypatch.chdir(MOONSHOT_CORE_ROOT)
    monkeypatch.delenv(be.BENCHMARK_EXTENSIONS_DIR_ENV, raising=False)
    provider_id, model_id, cfg_id = _add_provider_with_config("benchmark_extension_openai_adapter")

    with patch.object(be, "DOCKER_DATA_DIR", Path("/nonexistent-moonshot-dir")):
        with pytest.raises(DatabaseConnectorConfigError, match="No connector adapter mapping"):
            DatabaseConnectorConfigService().build_connector_entity(
                llm_provider_id=provider_id,
                llm_provider_model_id=model_id,
                llm_provider_model_config_id=cfg_id,
            )


@pytest.mark.asyncio
async def test_connection_test_resolves_extension_adapter_module(monkeypatch, test_db_env):
    from application.dto.provider_dto import TestLlmProviderConnectionBody
    from application.services.llm_provider_connection_test_service import (
        LlmProviderConnectionTestService,
    )

    monkeypatch.chdir(MOONSHOT_CORE_ROOT)
    monkeypatch.setenv(be.BENCHMARK_EXTENSIONS_DIR_ENV, str(EXAMPLE_EXTENSIONS_DIR))
    provider_id, _, _ = _add_provider_with_config("benchmark_extension_openai_adapter")
    captured = {}

    class _FakeAdapter:
        DEFAULT_CONFIG_PAIRS: dict = {}

        def configure(self, entity):
            captured["adapter_module"] = entity.connector_adapter

        async def get_response(self, prompt):
            return MagicMock(response="OK")

    with patch(
        "application.services.llm_provider_connection_test_service.ModuleLoader.load",
        return_value=(_FakeAdapter(), "id"),
    ):
        result = await LlmProviderConnectionTestService().test_connection(
            TestLlmProviderConnectionBody(llm_provider_id=provider_id, model_name="m", api_key="k")
        )

    assert result.success is True
    assert captured["adapter_module"] == "benchmark_extension_openai_adapter"
