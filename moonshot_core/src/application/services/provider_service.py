from domain.services.logger import get_logger

##TODO: Remove this service and use the SQLAlchemy implementation instead
## THIS IS MARKED FOR DELETION

from typing import Dict, List, Optional, Type
from datetime import datetime

from adapters.connector.openai_adapter import OpenAIAdapter
from adapters.connector.openrouter_adapter import OpenRouterAdapter
from adapters.connector.together_adapter import TogetherAdapter
from adapters.driven.repository.sqlalchemy.llm_provider_adapter import (
    LLMProviderAdapter,
)
from adapters.driven.repository.sqlalchemy.llm_provider_models import (
    LLMProviderModel,
    LLMProviderModelModel,
    LLMProviderEndpointConfigModel,
    LLMProviderModelConfigModel,
    LLMProviderModelConfigParametersModel,
    LLMProviderApiKeyModel,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from domain.entities.provider_entity import ProviderEntity
from domain.entities.model_config_entity import ModelConfigEntity
from application.dto.provider_dto import ProviderDTO
from application.dto.model_config_dto import (
    ModelConfigDTO,
    LLMProviderDetailsDTO,
    LLMProviderEndpointConfigInfoDTO,
    LLMProviderModelInfoDTO,
    ProviderDatabaseConfigsDTO,
)
from application.services.sqlite_adapter import SQLiteAdapter
from domain.ports.connector_port import ConnectorPort
from domain.services.feature_flags import (
    OPENROUTER_ADAPTER_SYSTEM_NAME,
    is_openrouter_enabled,
)


def get_adapter_by_system_name() -> Dict[str, Type[ConnectorPort]]:
    """Map llm_provider.system_name to ConnectorPort class (OpenRouter gated by feature flag)."""
    mapping: Dict[str, Type[ConnectorPort]] = {
        OpenAIAdapter.SYSTEM_NAME: OpenAIAdapter,
        TogetherAdapter.SYSTEM_NAME: TogetherAdapter,
    }
    if is_openrouter_enabled():
        mapping[OpenRouterAdapter.SYSTEM_NAME] = OpenRouterAdapter
    return mapping


# Backward-compatible name; prefer get_adapter_by_system_name() for flag-aware lookups.
_ADAPTER_BY_SYSTEM_NAME: Dict[str, Type[ConnectorPort]] = get_adapter_by_system_name()


class ProviderService:
    """
    Service class for managing provider operations.

    This service provides high-level operations for managing providers,
    converting between database representations and domain entities.
    """

    def __init__(self):
        """
        Initialize the provider service.

        Args:
            provider_repository (ProviderRepository): The repository for provider data access.
        """
        self.provider_repository = LLMProviderAdapter()
        self.logger = get_logger(__name__)
        self._session_manager = SessionManager.get_instance()

    def _provider_entity_to_dto(self, entity: ProviderEntity) -> ProviderDTO:
        """Convert ProviderEntity to ProviderDTO."""
        return ProviderDTO(
            id=entity.id,
            name=entity.name,
            system_name=entity.system_name,
            version=entity.version,
            defaultModel=entity.defaultModel,
            modelTextboxExplanation=entity.modelTextboxExplanation,
            defaultConfigPairs=entity.defaultConfigPairs,
            modelToken=entity.modelToken,
        )

    def _enrich_dto_with_adapter_defaults(self, dto: ProviderDTO) -> ProviderDTO:
        """
        Fill defaultModel, modelTextboxExplanation, defaultConfigPairs, and modelToken from the
        matching ConnectorPort class metadata when DB-derived values are empty.
        """
        adapter_cls = get_adapter_by_system_name().get(dto.system_name)
        if adapter_cls is None:
            return dto
        seed = adapter_cls.provider_seed_definition()
        if not dto.defaultModel:
            dto.defaultModel = str(seed.get("defaultModel", "") or "")
        if not dto.modelTextboxExplanation:
            dto.modelTextboxExplanation = str(
                seed.get("modelTextboxExplanation", "") or ""
            )
        if not dto.defaultConfigPairs:
            pairs = seed.get("defaultConfigPairs") or {}
            dto.defaultConfigPairs = dict(pairs) if pairs else {}
        if not dto.modelToken:
            dto.modelToken = str(seed.get("modelToken", "") or "")
        return dto

    def _model_config_entity_to_dto(self, entity: ModelConfigEntity) -> ModelConfigDTO:
        """Convert ModelConfigEntity to ModelConfigDTO."""
        return ModelConfigDTO(
            id=entity.id,
            name=entity.name,
            modelname=entity.modelname,
            providerID=entity.providerID,
            provider_version=entity.provider_version,
            savedConfigPairs=entity.savedConfigPairs,
            lastUpdated=entity.lastUpdated,
        )

    def _dto_to_provider_entity(self, dto: ProviderDTO) -> ProviderEntity:
        """Convert ProviderDTO to ProviderEntity."""
        return ProviderEntity(
            id=dto.id,
            name=dto.name,
            system_name=dto.system_name,
            version=dto.version,
            defaultModel=dto.defaultModel,
            modelTextboxExplanation=dto.modelTextboxExplanation,
            defaultConfigPairs=dto.defaultConfigPairs,
            modelToken=dto.modelToken,
        )

    def _dto_to_model_config_entity(self, dto: ModelConfigDTO) -> ModelConfigEntity:
        """Convert ModelConfigDTO to ModelConfigEntity."""
        # Ensure lastUpdated is present; if missing, use now
        last_updated = dto.lastUpdated if dto.lastUpdated else datetime.utcnow()
        return ModelConfigEntity(
            id=dto.id,
            name=dto.name,
            modelname=dto.modelname,
            providerID=dto.providerID,
            provider_version=dto.provider_version,
            savedConfigPairs=dto.savedConfigPairs,
            lastUpdated=last_updated,
        )

    def _database_model_config_dtos_for_provider(
        self,
        session,
        provider: LLMProviderModel,
    ) -> List[ModelConfigDTO]:
        """Build ModelConfigDTO rows from relational llm_provider_model_config (+ parameters)."""
        models: List[LLMProviderModelModel] = (
            session.query(LLMProviderModelModel)
            .filter(LLMProviderModelModel.llm_provider_id == provider.id)
            .all()
        )
        model_id_to_name: Dict[int, str] = {int(m.id): m.name for m in models}
        if not model_id_to_name:
            return []
        model_ids = list(model_id_to_name.keys())
        config_rows: List[LLMProviderModelConfigModel] = (
            session.query(LLMProviderModelConfigModel)
            .filter(LLMProviderModelConfigModel.model_id.in_(model_ids))
            .order_by(LLMProviderModelConfigModel.id)
            .all()
        )
        if not config_rows:
            return []
        config_ids = [int(r.id) for r in config_rows]
        param_rows: List[LLMProviderModelConfigParametersModel] = (
            session.query(LLMProviderModelConfigParametersModel)
            .filter(LLMProviderModelConfigParametersModel.config_id.in_(config_ids))
            .all()
        )
        pairs_by_config: Dict[int, Dict[str, str]] = {}
        for prow in param_rows:
            cid = int(prow.config_id)
            pairs_by_config.setdefault(cid, {})[str(prow.key)] = str(prow.value)

        config_dtos: List[ModelConfigDTO] = []
        for row in config_rows:
            mid = row.model_id
            if mid is None:
                continue
            mid_int = int(mid)
            modelname = model_id_to_name.get(mid_int, "")
            cid = int(row.id)
            config_dtos.append(
                ModelConfigDTO(
                    id=str(cid),
                    name=str(row.name),
                    modelname=modelname,
                    modelId=mid_int,
                    providerID=provider.system_name,
                    savedConfigPairs=pairs_by_config.get(cid, {}),
                    lastUpdated=row.updated_dt,
                )
            )
        return config_dtos

    def list_providers(self) -> List[ProviderDTO]:
        """
        List all available providers.

        Returns:
            List[ProviderDTO]: A list of all provider DTOs.
        """
        self.logger.info("Listing all providers")
        entities = self.provider_repository.list_providers()
        return [
            self._enrich_dto_with_adapter_defaults(self._provider_entity_to_dto(entity))
            for entity in entities
            if is_openrouter_enabled()
            or entity.system_name != OPENROUTER_ADAPTER_SYSTEM_NAME
        ]

    def add_provider(self, provider: ProviderDTO) -> ProviderDTO:
        """
        Add a new provider.

        Args:
            provider (ProviderDTO): The provider DTO to add.

        Returns:
            ProviderDTO: The added provider DTO with any generated fields.
        """
        self.logger.info(
            f"Adding provider: {provider.name} ({provider.system_name} v{provider.version})"
        )
        added_entity = self.provider_repository.add_provider(
            name=provider.name,
            system_name=provider.system_name,
            version=provider.version,
        )
        return self._provider_entity_to_dto(added_entity)

    def get_model_configs_by_provider_id(
        self, provider_id: int
    ) -> List[ModelConfigDTO]:
        """
        Get all model configurations associated with a provider ID.

        Args:
            provider_id (int): The numeric provider ID.

        Returns:
            List[ModelConfigDTO]: List of model configuration DTOs.
        """
        self.logger.info(f"Listing model configs by provider ID: {provider_id}")
        sqlite = SQLiteAdapter()
        entities = sqlite.get_all_model_config_entity(provider_id)
        return [self._model_config_entity_to_dto(entity) for entity in entities]

    def create_model_config(self, model_config: ModelConfigDTO) -> ModelConfigDTO:
        """
        Create a new model configuration.

        Args:
            model_config (ModelConfigDTO): The model configuration to create.

        Returns:
            ModelConfigDTO: The created model configuration DTO.
        """
        self.logger.info(f"Creating model config: {model_config.name}")
        entity = self._dto_to_model_config_entity(model_config)
        sqlite = SQLiteAdapter()
        created_entity = sqlite.add_model_config_entity(entity)
        return self._model_config_entity_to_dto(created_entity)

    def update_model_config(self, model_config: ModelConfigDTO) -> ModelConfigDTO:
        """
        Update an existing model configuration (matched by name).

        Args:
            model_config (ModelConfigDTO): The model configuration with updates.

        Returns:
            ModelConfigDTO: The updated model configuration DTO.
        """
        self.logger.info(f"Updating model config: {model_config.name}")
        entity = self._dto_to_model_config_entity(model_config)
        sqlite = SQLiteAdapter()
        updated_entity = sqlite.update_model_config_entity(entity)
        return self._model_config_entity_to_dto(updated_entity)

    def delete_model_config(self, config_id: str) -> bool:
        """
        Delete a model configuration (by ID or name).

        Args:
            config_id (str): The config ID or name to delete.

        Returns:
            bool: True if deleted, False otherwise.
        """
        self.logger.info(f"Deleting model config: {config_id}")
        sqlite = SQLiteAdapter()
        return sqlite.delete_model_config_entity(config_id)

    def get_latest_provider_details_by_system_name(
        self,
        system_name: str,
    ) -> Optional[LLMProviderDetailsDTO]:
        """
        Return the latest-version provider and its related models and endpoint configs for a system_name.

        Args:
            system_name: The llm_provider.system_name to look up.

        Returns:
            LLMProviderDetailsDTO if a provider exists, otherwise None.
        """
        self.logger.info(
            "Fetching latest provider details for system_name=%s", system_name
        )
        try:
            with self._session_manager.get_session() as session:
                provider_model: Optional[LLMProviderModel] = (
                    session.query(LLMProviderModel)
                    .filter(LLMProviderModel.system_name == system_name)
                    .order_by(LLMProviderModel.version.desc())
                    .first()
                )

                if provider_model is None:
                    self.logger.warning(
                        "No provider found for system_name=%s", system_name
                    )
                    return None

                provider_entity = self.provider_repository._model_to_entity(  # type: ignore[attr-defined]
                    provider_model
                )
                provider_dto = self._enrich_dto_with_adapter_defaults(
                    self._provider_entity_to_dto(provider_entity)
                )

                models: list[LLMProviderModelModel] = (
                    session.query(LLMProviderModelModel)
                    .filter(LLMProviderModelModel.llm_provider_id == provider_model.id)
                    .all()
                )
                endpoint_configs: list[LLMProviderEndpointConfigModel] = (
                    session.query(LLMProviderEndpointConfigModel)
                    .filter(
                        LLMProviderEndpointConfigModel.llm_provider_id
                        == provider_model.id
                    )
                    .all()
                )

                model_dtos = [
                    LLMProviderModelInfoDTO(
                        id=m.id,
                        name=m.name,
                        create_dt=m.create_dt,
                    )
                    for m in models
                ]
                endpoint_config_dtos = [
                    LLMProviderEndpointConfigInfoDTO(
                        id=e.id,
                        name=e.name,
                    )
                    for e in endpoint_configs
                ]

                db_model_cfgs = self._database_model_config_dtos_for_provider(
                    session, provider_model
                )

                api_key_configured = (
                    session.query(LLMProviderApiKeyModel)
                    .filter(LLMProviderApiKeyModel.llm_provider_id == provider_model.id)
                    .count()
                    > 0
                )

                return LLMProviderDetailsDTO(
                    provider=provider_dto,
                    models=model_dtos,
                    endpoint_configs=endpoint_config_dtos,
                    config_params=None,
                    database_model_configs=db_model_cfgs,
                    api_key_configured=api_key_configured,
                )
        except Exception as exc:
            self.logger.error(
                "Error fetching latest provider details for system_name=%s: %s",
                system_name,
                exc,
            )
            return None

    def list_providers_with_database_model_configs(
        self,
    ) -> List[ProviderDatabaseConfigsDTO]:
        """
        List every llm_provider row (ordered by id) with model configs from the relational schema only.

        For each provider, loads llm_provider_model rows, then llm_provider_model_config rows whose
        model_id references those models (configs with NULL model_id are omitted). For each config,
        savedConfigPairs is built solely from llm_provider_model_config_parameters rows for that
        config_id. providerID on each ModelConfigDTO is llm_provider.system_name; modelname is
        llm_provider_model.name.
        """
        self.logger.info("Listing providers with database-backed model configs")
        out: List[ProviderDatabaseConfigsDTO] = []

        with self._session_manager.get_session() as session:
            providers: List[LLMProviderModel] = (
                session.query(LLMProviderModel).order_by(LLMProviderModel.id).all()
            )
            for provider in providers:
                config_dtos = self._database_model_config_dtos_for_provider(
                    session, provider
                )
                out.append(
                    ProviderDatabaseConfigsDTO(
                        providerName=provider.name,
                        configs=config_dtos,
                    )
                )

        return out
