"""Resolve ConnectorEntity from llm_provider / model / model_config DB rows (no YAML)."""

from __future__ import annotations

from typing import Dict

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderModel,
    LLMProviderModelConfigModel,
    LLMProviderModelConfigParametersModel,
    LLMProviderModelModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.provider_connector_env_key_service import ProviderConnectorEnvKeyService
from domain.entities.connector_entity import ConnectorEntity
from domain.services.enums.module_types import ModuleTypes
from domain.services.feature_flags import (
    OPENROUTER_ADAPTER_SYSTEM_NAME,
    is_openrouter_enabled,
)
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

logger = configure_logger(__name__)


def get_system_name_to_adapter_module() -> dict[str, str]:
    """llm_provider.system_name (DB) -> connector module name (OpenRouter gated by feature flag)."""
    mapping = {
        "together_ai": "together_adapter",
        "openai_adapter": "openai_adapter",
        "together_adapter": "together_adapter",
    }
    if is_openrouter_enabled():
        mapping[OPENROUTER_ADAPTER_SYSTEM_NAME] = OPENROUTER_ADAPTER_SYSTEM_NAME
    return mapping


# Backward-compatible name; prefer get_system_name_to_adapter_module() for flag-aware lookups.
SYSTEM_NAME_TO_ADAPTER_MODULE: dict[str, str] = get_system_name_to_adapter_module()


def _adapters_that_resolve_api_keys_internally() -> frozenset[str]:
    modules = {"openai_adapter", "together_adapter"}
    if is_openrouter_enabled():
        modules.add(OPENROUTER_ADAPTER_SYSTEM_NAME)
    return frozenset(modules)


class DatabaseConnectorConfigError(ValueError):
    """Invalid or inconsistent llm_provider / model / model_config ids."""


class DatabaseConnectorConfigService:
    """Build a ConnectorEntity for benchmark execution from relational rows."""

    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()

    def build_connector_entity(
        self,
        *,
        llm_provider_id: int,
        llm_provider_model_id: int,
        llm_provider_model_config_id: int,
    ) -> ConnectorEntity:
        with self._session_manager.get_session() as session:
            provider = (
                session.query(LLMProviderModel)
                .filter(LLMProviderModel.id == llm_provider_id)
                .first()
            )
            if provider is None:
                raise DatabaseConnectorConfigError(
                    f"No llm_provider with id={llm_provider_id}"
                )

            model = (
                session.query(LLMProviderModelModel)
                .filter(LLMProviderModelModel.id == llm_provider_model_id)
                .first()
            )
            if model is None:
                raise DatabaseConnectorConfigError(
                    f"No llm_provider_model with id={llm_provider_model_id}"
                )
            if int(model.llm_provider_id) != int(llm_provider_id):
                raise DatabaseConnectorConfigError(
                    f"llm_provider_model {llm_provider_model_id} does not belong to "
                    f"llm_provider {llm_provider_id}"
                )

            cfg = (
                session.query(LLMProviderModelConfigModel)
                .filter(LLMProviderModelConfigModel.id == llm_provider_model_config_id)
                .first()
            )
            if cfg is None:
                raise DatabaseConnectorConfigError(
                    f"No llm_provider_model_config with id={llm_provider_model_config_id}"
                )
            if cfg.model_id is None or int(cfg.model_id) != int(llm_provider_model_id):
                raise DatabaseConnectorConfigError(
                    f"llm_provider_model_config {llm_provider_model_config_id} does not "
                    f"belong to llm_provider_model {llm_provider_model_id}"
                )

            adapter_module = get_system_name_to_adapter_module().get(provider.system_name)
            if adapter_module is None:
                raise DatabaseConnectorConfigError(
                    f"No connector adapter mapping for provider system_name={provider.system_name!r}"
                )

            try:
                adapter_instance, _ = ModuleLoader.load(adapter_module, ModuleTypes.CONNECTOR)
                adapter_cls = adapter_instance.__class__
                default_pairs: Dict[str, str] = dict(getattr(adapter_cls, "DEFAULT_CONFIG_PAIRS", {}))
            except Exception as exc:
                logger.error("Failed to load connector adapter %s: %s", adapter_module, exc)
                raise DatabaseConnectorConfigError(
                    f"Failed to load connector adapter {adapter_module!r}"
                ) from exc

            param_rows = (
                session.query(LLMProviderModelConfigParametersModel)
                .filter(
                    LLMProviderModelConfigParametersModel.config_id == llm_provider_model_config_id
                )
                .all()
            )
            merged: Dict[str, str] = {**default_pairs}
            for prow in param_rows:
                merged[str(prow.key)] = str(prow.value)

            model_endpoint = str(merged.pop("base_url", "") or "").strip()
            model_name = str(model.name)

        # OpenAI / Together / OpenRouter (when enabled) load API keys from llm_provider via
        # ConnectorPort SYSTEM_NAME / VERSION.
        if adapter_module not in _adapters_that_resolve_api_keys_internally():
            ProviderConnectorEnvKeyService(self._session_manager).ensure_provider_api_key_in_environment(
                llm_provider_id=llm_provider_id,
                adapter_module=adapter_module,
            )

        return ConnectorEntity(
            connector_adapter=adapter_module,
            model=model_name,
            model_endpoint=model_endpoint,
            params=merged,
        )
