from typing import Optional

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from application.ports.custom_app_repository import CustomAppRepository
from domain.services.logger import configure_logger


class CustomAppSeedService:
    """Seed built-in custom apps used by benchmark model selection."""

    DEFAULT_CUSTOM_APPS = ("API Connector",)

    def __init__(self, custom_app_repository: Optional[CustomAppRepository] = None) -> None:
        self.logger = configure_logger(__name__)
        self.custom_app_repository = custom_app_repository or CustomAppAdapter()

    def seed_hardcoded_custom_apps(self) -> None:
        """Idempotently seed hardcoded custom-app rows."""
        self.logger.info("Seeding hardcoded custom apps")
        existing_names = {app.name for app in self.custom_app_repository.list_all()}

        for app_name in self.DEFAULT_CUSTOM_APPS:
            if app_name in existing_names:
                self.logger.info("Skipping custom app %r (already exists)", app_name)
                continue
            self.custom_app_repository.add(app_name)
            self.logger.info("Inserted custom app %r", app_name)
