from __future__ import annotations

import os
from typing import Any

from application.services.bedrock_mantle_web_search_service import run_web_search_completion
from application.services.provider_connector_env_key_service import ProviderConnectorEnvKeyService
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity
from domain.ports.connector_port import ConnectorPort
from domain.services.logger import configure_logger

logger = configure_logger(__name__)


class BedrockMantleWebSearchAdapter(ConnectorPort):
    PROVIDER_NAME = "Bedrock Web Search"
    SYSTEM_NAME = "bedrock_mantle_web_search"
    VERSION = 1
    DEFAULT_MODEL = "openai.gpt-5.5"
    MODEL_TEXTBOX_EXPLANATION = (
        "Bedrock OpenAI model id on Mantle (e.g. openai.gpt-5.5, openai.gpt-6-sol). "
        "Web search is enabled for all calls."
    )
    DEFAULT_CONFIG_PAIRS = {
        "region": "us-east-1",
    }

    def configure(self, connector_entity: ConnectorEntity) -> None:
        self.connector_entity = connector_entity
        params = connector_entity.params
        self._region = str(params.get("region") or "us-east-1").strip()
        self._model_id = str(
            params.get("model_id") or connector_entity.model or self.DEFAULT_MODEL
        ).strip()

        system_name, version = type(self).require_system_name_and_version()
        params_key = str(params.get("api_key") or "").strip()
        if params_key:
            self._api_key = params_key
        else:
            db_key = ProviderConnectorEnvKeyService().get_plain_api_key_for_provider_system_name(
                provider_system_name=system_name,
                version=version,
            )
            if db_key and db_key.strip():
                self._api_key = db_key.strip()
            else:
                self._api_key = os.getenv("BEDROCK_MANTLE_API_KEY") or ""
            if not self._api_key:
                logger.warning(
                    "[BedrockMantleWebSearchAdapter] No API key from database or "
                    "BEDROCK_MANTLE_API_KEY for system_name=%s",
                    system_name,
                )

    async def get_response(self, prompt: Any) -> ConnectorResponseEntity:
        connector_prompt = (
            f"{self.connector_entity.connector_pre_prompt}{prompt}"
            f"{self.connector_entity.connector_post_prompt}"
        )
        result = await run_web_search_completion(
            prompt=str(connector_prompt),
            region=self._region,
            model_id=self._model_id,
            api_key=self._api_key,
        )
        return ConnectorResponseEntity(response=result.text)
