"""Create/update custom_app_config and parameter rows."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from adapters.driven.repository.sqlalchemy.custom_app_config_adapter import (
    CustomAppConfigAdapter,
)
from adapters.driven.repository.sqlalchemy.session_manager import SessionManager
from application.dto.custom_app_config_dto import (
    CreateCustomAppConfigBody,
    CustomAppConfigResponseDTO,
    CustomAppResponseDTO,
    CreateCustomAppBody,
    UpdateCustomAppConfigBody,
)
from application.ports.custom_app_config_repository import CustomAppConfigRepository
from application.ports.custom_app_repository import CustomAppRepository
from application.services.custom_app_config_secret_service import (
    CustomAppConfigSecretService,
)
from domain.services.logger import configure_logger


class DatabaseCustomAppConfigNotFoundError(Exception):
    """No custom_app_config row for the given id."""


class DatabaseCustomAppConfigConflictError(Exception):
    """Unique constraint violation."""


class DatabaseCustomAppConfigBadRequestError(Exception):
    """Invalid custom_app_id or request payload."""


class DatabaseCustomAppService:
    """CRUD for custom_app rows."""

    def __init__(
        self,
        repository: CustomAppRepository | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        self._repository = repository or CustomAppAdapter(session_manager)
        self._logger = configure_logger(__name__)

    def list_apps(self) -> list[CustomAppResponseDTO]:
        return [
            CustomAppResponseDTO.model_validate(e.model_dump())
            for e in self._repository.list_all()
        ]

    def create_app(self, body: CreateCustomAppBody) -> CustomAppResponseDTO:
        entity = self._repository.add(body.name.strip())
        return CustomAppResponseDTO.model_validate(entity.model_dump())


class DatabaseCustomAppConfigService:
    """Insert and update database-backed custom app configs."""

    def __init__(
        self,
        config_repository: CustomAppConfigRepository | None = None,
        app_repository: CustomAppRepository | None = None,
        secret_service: CustomAppConfigSecretService | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        self._config_repository = config_repository or CustomAppConfigAdapter(session_manager)
        self._app_repository = app_repository or CustomAppAdapter(session_manager)
        self._secret_service = secret_service or CustomAppConfigSecretService(
            session_manager=session_manager
        )
        self._logger = configure_logger(__name__)

    def list_configs(self, custom_app_id: int) -> list[CustomAppConfigResponseDTO]:
        if self._app_repository.get_by_id(custom_app_id) is None:
            raise DatabaseCustomAppConfigBadRequestError(
                f"No custom_app with id={custom_app_id}"
            )
        configs = self._config_repository.list_by_app_id(custom_app_id)
        return [self._to_dto(c.id) for c in configs if c.id is not None]

    def create(
        self, custom_app_id: int, body: CreateCustomAppConfigBody
    ) -> CustomAppConfigResponseDTO:
        try:
            entity = self._config_repository.create(
                custom_app_id=custom_app_id,
                name=body.name.strip(),
                parameters=body.savedConfigPairs,
            )
            if entity.id is None:
                raise RuntimeError("create did not return config id")
            return self._to_dto(entity.id)
        except IntegrityError as exc:
            raise DatabaseCustomAppConfigConflictError(
                "Database constraint violation while creating custom app config"
            ) from exc
        except ValueError as exc:
            raise DatabaseCustomAppConfigBadRequestError(str(exc)) from exc

    def update(
        self, config_id: int, body: UpdateCustomAppConfigBody
    ) -> CustomAppConfigResponseDTO:
        try:
            if self._config_repository.get_by_id(config_id) is None:
                raise DatabaseCustomAppConfigNotFoundError(
                    f"No custom_app_config with id={config_id}"
                )
            self._config_repository.update(
                config_id=config_id,
                name=body.name.strip(),
                parameters=body.savedConfigPairs,
            )
            return self._to_dto(config_id)
        except IntegrityError as exc:
            raise DatabaseCustomAppConfigConflictError(
                "Database constraint violation while updating custom app config"
            ) from exc
        except ValueError as exc:
            raise DatabaseCustomAppConfigBadRequestError(str(exc)) from exc

    def _to_dto(self, config_id: int) -> CustomAppConfigResponseDTO:
        entity = self._config_repository.get_by_id(config_id)
        if entity is None:
            raise DatabaseCustomAppConfigNotFoundError(
                f"No custom_app_config with id={config_id}"
            )
        params = self._config_repository.get_parameters(config_id)
        return CustomAppConfigResponseDTO(
            id=entity.id,
            custom_app_id=entity.custom_app_id,
            name=entity.name,
            savedConfigPairs=params,
            update_dt=entity.update_dt,
            api_key_configured=self._secret_service.is_secret_configured(
                config_id, "api_key"
            ),
        )
