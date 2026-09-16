"""Probe an LLM provider connector configuration with a short live chat request."""

from __future__ import annotations

from typing import Dict

from adapters.driven.repository.sqlalchemy.llm_provider_models import \
    LLMProviderModel
from adapters.driven.repository.sqlalchemy.session_manager import \
    SessionManager
from application.dto.provider_dto import (TestLlmProviderConnectionBody,
                                          TestLlmProviderConnectionResponseDTO)
from application.services.database_connector_config_service import \
    get_system_name_to_adapter_module
from application.services.provider_connector_env_key_service import \
    ProviderConnectorEnvKeyService
from domain.entities.connector_entity import ConnectorEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

CONNECTION_TEST_PROMPT = "Reply with OK."
RESPONSE_PREVIEW_MAX_CHARS = 500


class LlmProviderConnectionTestService:
    def __init__(
        self,
        session_manager: SessionManager | None = None,
        env_key_service: ProviderConnectorEnvKeyService | None = None,
    ) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()
        self._env_key_service = env_key_service or ProviderConnectorEnvKeyService(
            self._session_manager
        )

    def _resolve_api_key(self, body: TestLlmProviderConnectionBody) -> str:
        api_key = (body.api_key or "").strip()
        if api_key:
            return api_key
        stored = self._env_key_service.get_plain_api_key_for_provider(
            body.llm_provider_id
        )
        if stored and stored.strip():
            return stored.strip()
        raise ValueError("An API key is required to test the connection.")

    def _load_provider_system_name(self, llm_provider_id: int) -> str:
        with self._session_manager.get_session() as session:
            provider = (
                session.query(LLMProviderModel)
                .filter(LLMProviderModel.id == llm_provider_id)
                .first()
            )
            if provider is None:
                raise ValueError(f"No llm_provider with id={llm_provider_id}")
            return str(provider.system_name)

    def _build_connector_entity(
        self,
        *,
        adapter_module: str,
        model_name: str,
        saved_config_pairs: Dict[str, str],
        api_key: str,
    ) -> ConnectorEntity:
        try:
            adapter_instance, _ = ModuleLoader.load(
                adapter_module, ModuleTypes.CONNECTOR
            )
            adapter_cls = adapter_instance.__class__
            default_pairs: Dict[str, str] = dict(
                getattr(adapter_cls, "DEFAULT_CONFIG_PAIRS", {})
            )
        except Exception as exc:
            logger.error("Failed to load connector adapter %s: %s", adapter_module, exc)
            raise ValueError(
                f"Failed to load connector adapter {adapter_module!r}"
            ) from exc

        merged: Dict[str, str] = {**default_pairs, **dict(saved_config_pairs)}
        model_endpoint = str(merged.pop("base_url", "") or "").strip()
        merged["api_key"] = api_key

        return ConnectorEntity(
            connector_adapter=adapter_module,
            model=model_name.strip(),
            model_endpoint=model_endpoint,
            params=merged,
        )

    @staticmethod
    def _preview_response(response_text: str) -> str:
        text = (response_text or "").strip()
        if len(text) <= RESPONSE_PREVIEW_MAX_CHARS:
            return text
        return text[:RESPONSE_PREVIEW_MAX_CHARS] + "…"

    async def test_connection(
        self, body: TestLlmProviderConnectionBody
    ) -> TestLlmProviderConnectionResponseDTO:
        model_name = (body.model_name or "").strip()
        if not model_name:
            raise ValueError("A model name is required to test the connection.")

        api_key = self._resolve_api_key(body)
        system_name = self._load_provider_system_name(body.llm_provider_id)
        adapter_module = get_system_name_to_adapter_module().get(system_name)
        if adapter_module is None:
            raise ValueError(
                f"No connector adapter mapping for provider system_name={system_name!r}"
            )

        entity = self._build_connector_entity(
            adapter_module=adapter_module,
            model_name=model_name,
            saved_config_pairs=body.savedConfigPairs or {},
            api_key=api_key,
        )

        try:
            adapter_instance, _ = ModuleLoader.load(
                entity.connector_adapter, ModuleTypes.CONNECTOR
            )
        except Exception as exc:
            logger.error(
                "Failed to load connector adapter %s: %s",
                entity.connector_adapter,
                exc,
            )
            return TestLlmProviderConnectionResponseDTO(
                success=False,
                error=f"Failed to load connector adapter {entity.connector_adapter!r}",
            )

        adapter: ConnectorPort = adapter_instance
        try:
            adapter.configure(entity)
        except ValueError as exc:
            return TestLlmProviderConnectionResponseDTO(success=False, error=str(exc))
        except Exception as exc:
            logger.error("LLM provider connection configure failed: %s", exc)
            return TestLlmProviderConnectionResponseDTO(success=False, error=str(exc))

        try:
            response_entity = await adapter.get_response(CONNECTION_TEST_PROMPT)
        except Exception as exc:
            logger.error("LLM provider connection test failed: %s", exc)
            return TestLlmProviderConnectionResponseDTO(
                success=False,
                error=str(exc),
            )

        preview = self._preview_response(getattr(response_entity, "response", "") or "")
        return TestLlmProviderConnectionResponseDTO(
            success=True,
            response_preview=preview or None,
        )
