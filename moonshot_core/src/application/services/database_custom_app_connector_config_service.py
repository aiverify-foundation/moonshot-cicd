"""Resolve ConnectorEntity from custom_app / custom_app_config DB rows."""

from __future__ import annotations

from typing import Dict

from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    CustomAppConfigModel,
    CustomAppConfigParametersModel,
    CustomAppModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.services.custom_app_config_secret_service import (
    CustomAppConfigSecretService,
)
from domain.entities.connector_entity import ConnectorEntity
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.logger import configure_logger

logger = configure_logger(__name__)

DEFAULT_CONNECTOR_ADAPTER = "custom_api_connector_adapter"


class DatabaseCustomAppConnectorConfigError(ValueError):
    """Invalid or inconsistent custom_app / custom_app_config ids."""


class DatabaseCustomAppConnectorConfigService:
    """Build a ConnectorEntity for benchmark execution from custom app rows."""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        secret_service: CustomAppConfigSecretService | None = None,
    ) -> None:
        self._session_manager = session_manager or SessionManager.get_instance()
        self._secret_service = secret_service or CustomAppConfigSecretService(
            session_manager=session_manager
        )

    def build_connector_entity(
        self,
        *,
        custom_app_id: int,
        custom_app_config_id: int,
    ) -> ConnectorEntity:
        with self._session_manager.get_session() as session:
            app = (
                session.query(CustomAppModel)
                .filter(CustomAppModel.id == custom_app_id)
                .first()
            )
            if app is None:
                raise DatabaseCustomAppConnectorConfigError(
                    f"No custom_app with id={custom_app_id}"
                )

            cfg = (
                session.query(CustomAppConfigModel)
                .filter(CustomAppConfigModel.id == custom_app_config_id)
                .first()
            )
            if cfg is None:
                raise DatabaseCustomAppConnectorConfigError(
                    f"No custom_app_config with id={custom_app_config_id}"
                )
            if int(cfg.custom_app_id) != int(custom_app_id):
                raise DatabaseCustomAppConnectorConfigError(
                    f"custom_app_config {custom_app_config_id} does not belong to "
                    f"custom_app {custom_app_id}"
                )

            param_rows = (
                session.query(CustomAppConfigParametersModel)
                .filter(CustomAppConfigParametersModel.config_id == custom_app_config_id)
                .all()
            )
            merged: Dict[str, str] = {str(p.key): str(p.value) for p in param_rows}

        adapter_module = merged.pop(
            "connector_adapter", DEFAULT_CONNECTOR_ADAPTER
        ).strip() or DEFAULT_CONNECTOR_ADAPTER

        try:
            adapter_instance, _ = ModuleLoader.load(adapter_module, ModuleTypes.CONNECTOR)
            adapter_cls = adapter_instance.__class__
            default_pairs: Dict[str, str] = dict(
                getattr(adapter_cls, "DEFAULT_CONFIG_PAIRS", {})
            )
        except Exception as exc:
            logger.error("Failed to load connector adapter %s: %s", adapter_module, exc)
            raise DatabaseCustomAppConnectorConfigError(
                f"Failed to load connector adapter {adapter_module!r}"
            ) from exc

        params = {**default_pairs, **merged}

        secrets = self._secret_service.get_all_decrypted_secrets(custom_app_config_id)
        params.update(secrets)

        model_endpoint = str(params.pop("base_url", "") or "").strip()

        return ConnectorEntity(
            connector_adapter=adapter_module,
            model="",
            model_endpoint=model_endpoint,
            params=params,
        )
