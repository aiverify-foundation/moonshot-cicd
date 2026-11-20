from domain.services.logger import get_logger
from typing import Optional

from adapters.driven.repository.sqlalchemy.custom_app_adapter import CustomAppAdapter
from application.ports.custom_app_repository import CustomAppRepository
from domain.services.enums.feature_flag_names import FeatureFlagNames
from domain.services.feature_flags import FeatureFlags

AWS_BEDROCK_API_APP_NAME = "AWS Bedrock API Connector"


class CustomAppSeedService:
    """Seed built-in custom apps used by benchmark model selection."""

    ALWAYS_SEEDED_CUSTOM_APPS = ("API Connector",)

    def __init__(self, custom_app_repository: Optional[CustomAppRepository] = None) -> None:
        self.logger = get_logger(__name__)
        self.custom_app_repository = custom_app_repository or CustomAppAdapter()

    def _custom_apps_to_seed(self) -> tuple[str, ...]:
        apps = list(self.ALWAYS_SEEDED_CUSTOM_APPS)
        if FeatureFlags().is_enabled(FeatureFlagNames.AIVET_OCT2026_MOON803):
            apps.append(AWS_BEDROCK_API_APP_NAME)
        return tuple(apps)

    def seed_hardcoded_custom_apps(self) -> None:
        """Idempotently seed hardcoded custom-app rows."""
        self.logger.info("Seeding hardcoded custom apps")
        existing_names = {app.name for app in self.custom_app_repository.list_all()}

        for app_name in self._custom_apps_to_seed():
            if app_name in existing_names:
                self.logger.info("Skipping custom app %r (already exists)", app_name)
                continue
            self.custom_app_repository.add(app_name)
            self.logger.info("Inserted custom app %r", app_name)
